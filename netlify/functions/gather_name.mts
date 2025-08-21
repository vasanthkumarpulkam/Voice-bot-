import type { Context, Config } from "@netlify/functions";
import { VoiceResponse } from 'twilio/lib/twiml/VoiceResponse';

export default async (req: Request, context: Context) => {
  if (req.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 });
  }

  try {
    // Parse form data from Twilio
    const formData = await req.formData();
    const url = new URL(req.url);
    const callSid = url.searchParams.get('sid') || formData.get('CallSid') as string || '';
    const nameCompany = (formData.get('SpeechResult') as string || '').trim();
    
    console.log(`Gathered name/company: ${nameCompany}`);

    // TODO: Store in database
    // await updateCall(callSid, { caller_name: nameCompany });

    // Create TwiML response
    const twiml = new VoiceResponse();
    const gather = twiml.gather({
      input: 'speech',
      action: `${getBaseUrl(req)}/route?sid=${callSid}`,
      method: 'POST',
      speechTimeout: 'auto',
      timeout: 8
    });
    
    gather.say("Thanks. Briefly, what is this regarding?");
    twiml.redirect(`${getBaseUrl(req)}/gather_name?sid=${callSid}`);

    return new Response(twiml.toString(), {
      status: 200,
      headers: {
        'Content-Type': 'text/xml'
      }
    });

  } catch (error) {
    console.error('Error in gather_name function:', error);
    return new Response('Internal Server Error', { status: 500 });
  }
};

function getBaseUrl(req: Request): string {
  const url = new URL(req.url);
  return `${url.protocol}//${url.host}/.netlify/functions`;
}

export const config: Config = {
  path: "/gather_name"
};
