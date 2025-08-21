import type { Context, Config } from "@netlify/functions";
import { VoiceResponse } from 'twilio/lib/twiml/VoiceResponse';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: Netlify.env.get('OPENAI_API_KEY')
});

const SYSTEM_PROMPT = `You classify inbound phone calls for Vasanth. Return ONLY strict JSON with keys: 
caller_type (recruiter|family|friend|promotion|unknown), 
priority (high|medium|low), urgency_minutes (integer or null), action (connect_now|take_message). 
Rules: Recruiters are connect_now/high. Promotions/telemarketing -> low/take_message. 
Family emergencies -> high/connect_now, otherwise medium. Decide conservatively when unsure.`;

export default async (req: Request, context: Context) => {
  if (req.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 });
  }

  try {
    // Parse form data from Twilio
    const formData = await req.formData();
    const url = new URL(req.url);
    const callSid = url.searchParams.get('sid') || formData.get('CallSid') as string || '';
    const reason = (formData.get('SpeechResult') as string || '').trim();
    
    console.log(`Reason: ${reason}`);

    // TODO: Get caller name from database
    const nameCompany = "Unknown Caller"; // This would come from database

    // Classify the call using OpenAI
    const decision = await classifyCall(nameCompany, reason);
    console.log('Classification:', decision);

    // TODO: Update database with classification
    // await updateCall(callSid, { reason, ...decision });

    // Create TwiML response based on decision
    const twiml = new VoiceResponse();
    
    if (decision.action === 'connect_now') {
      twiml.say("Please hold while I connect you to Vasanth.");
      // In production, you would dial Vasanth's number here
      // twiml.dial(Netlify.env.get('VASANTH_PHONE_NUMBER'));
      twiml.say("Sorry, Vasanth is not available right now. Please leave a message after the beep.");
      twiml.record({
        action: `${getBaseUrl(req)}/recording?sid=${callSid}`,
        method: 'POST',
        maxLength: 60,
        finishOnKey: '#'
      });
    } else {
      twiml.say("Thanks for calling. Please leave a detailed message after the beep, and Vasanth will get back to you.");
      twiml.record({
        action: `${getBaseUrl(req)}/recording?sid=${callSid}`,
        method: 'POST',
        maxLength: 60,
        finishOnKey: '#'
      });
    }

    // Send SMS notification for high priority calls
    if (decision.priority === 'high') {
      // TODO: Send SMS notification
      console.log(`High priority call from ${nameCompany}: ${reason}`);
    }

    return new Response(twiml.toString(), {
      status: 200,
      headers: {
        'Content-Type': 'text/xml'
      }
    });

  } catch (error) {
    console.error('Error in route function:', error);
    
    // Fallback TwiML
    const twiml = new VoiceResponse();
    twiml.say("Sorry, there was an error processing your call. Please leave a message after the beep.");
    twiml.record({
      action: `${getBaseUrl(req)}/recording?sid=${req.url.split('sid=')[1]?.split('&')[0] || 'unknown'}`,
      method: 'POST',
      maxLength: 60,
      finishOnKey: '#'
    });
    
    return new Response(twiml.toString(), {
      status: 200,
      headers: {
        'Content-Type': 'text/xml'
      }
    });
  }
};

async function classifyCall(nameCompany: string, reason: string) {
  try {
    const text = `Caller info: ${nameCompany}\nReason: ${reason}`;
    
    const response = await openai.chat.completions.create({
      model: Netlify.env.get('OPENAI_MODEL') || 'gpt-3.5-turbo',
      temperature: 0.0,
      response_format: { type: "json_object" },
      messages: [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user", content: text }
      ]
    });

    const content = response.choices[0]?.message?.content;
    if (!content) throw new Error('No response from OpenAI');
    
    const data = JSON.parse(content);
    
    return {
      caller_type: data.caller_type || 'unknown',
      priority: data.priority || 'low',
      urgency_minutes: data.urgency_minutes || null,
      action: data.action || 'take_message'
    };

  } catch (error) {
    console.error('Classification error:', error);
    // Safe fallback
    return {
      caller_type: 'unknown',
      priority: 'low',
      urgency_minutes: null,
      action: 'take_message'
    };
  }
}

function getBaseUrl(req: Request): string {
  const url = new URL(req.url);
  return `${url.protocol}//${url.host}/.netlify/functions`;
}

export const config: Config = {
  path: "/route"
};
