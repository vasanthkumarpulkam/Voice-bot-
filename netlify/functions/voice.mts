import type { Context, Config } from "@netlify/functions";
import { VoiceResponse } from 'twilio/lib/twiml/VoiceResponse';

export default async (req: Request, context: Context) => {
  if (req.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 });
  }

  try {
    // Parse form data from Twilio
    const formData = await req.formData();
    const callSid = formData.get('CallSid') as string || '';
    const fromNumber = formData.get('From') as string || '';
    
    console.log(`Incoming call ${callSid} from ${fromNumber}`);

    // Create TwiML response
    const twiml = new VoiceResponse();
    const gather = twiml.gather({
      input: 'speech',
      action: `${getBaseUrl(req)}/gather_name?sid=${callSid}`,
      method: 'POST',
      speechTimeout: 'auto',
      timeout: 6
    });
    
    gather.say("Hi, you have reached Vasanth's assistant. I'll grab your name and company. What is your name and company?");
    twiml.redirect(`${getBaseUrl(req)}/voice`);

    return new Response(twiml.toString(), {
      status: 200,
      headers: {
        'Content-Type': 'text/xml'
      }
    });

  } catch (error) {
    console.error('Error in voice function:', error);
    return new Response('Internal Server Error', { status: 500 });
  }
};

function getBaseUrl(req: Request): string {
  const url = new URL(req.url);
  return `${url.protocol}//${url.host}/.netlify/functions`;
}

export const config: Config = {
  path: "/voice"
};
