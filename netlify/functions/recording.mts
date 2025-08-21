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
    const recordingUrl = formData.get('RecordingUrl') as string || '';
    
    console.log(`Recording completed for call ${callSid}: ${recordingUrl}`);

    // TODO: Store recording URL in database
    // await updateCall(callSid, { recording_url: recordingUrl });

    // Create final TwiML response
    const twiml = new VoiceResponse();
    twiml.say("Thank you for your message. Vasanth will get back to you soon. Goodbye!");
    twiml.hangup();

    return new Response(twiml.toString(), {
      status: 200,
      headers: {
        'Content-Type': 'text/xml'
      }
    });

  } catch (error) {
    console.error('Error in recording function:', error);
    
    // Fallback TwiML
    const twiml = new VoiceResponse();
    twiml.say("Thank you for calling. Goodbye!");
    twiml.hangup();
    
    return new Response(twiml.toString(), {
      status: 200,
      headers: {
        'Content-Type': 'text/xml'
      }
    });
  }
};

export const config: Config = {
  path: "/recording"
};
