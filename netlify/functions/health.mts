import type { Context, Config } from "@netlify/functions";

export default async (req: Request, context: Context) => {
  return new Response(JSON.stringify({
    status: "healthy",
    message: "Vasanth's AI Assistant is running on Netlify",
    timestamp: new Date().toISOString(),
    version: "2.0-netlify"
  }), {
    status: 200,
    headers: {
      'Content-Type': 'application/json'
    }
  });
};

export const config: Config = {
  path: "/"
};
