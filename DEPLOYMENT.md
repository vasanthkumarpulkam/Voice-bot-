# 🚀 Netlify Deployment Guide

Your voice bot has been converted to Node.js serverless functions for Netlify deployment!

## 📁 Project Structure

```
├── netlify/functions/          # Serverless functions
│   ├── voice.mts              # Main voice webhook
│   ├── gather_name.mts        # Collect caller info
│   ├── route.mts              # AI classification & routing
│   ├── recording.mts          # Handle recordings
│   └── health.mts             # Health check
├── index.html                 # Status page
├── package.json               # Node.js dependencies
├── netlify.toml               # Netlify configuration
└── DEPLOYMENT.md              # This file
```

## 🚀 Deploy to Netlify

### Method 1: Direct Git Deploy (Recommended)

1. **Push to GitHub** (click the Push button in top-right)

2. **Connect to Netlify:**
   - Go to [netlify.com](https://netlify.com)
   - Click "Add new site" → "Import from Git"
   - Select your GitHub repo: `vasanthkumarpulkam/Voice-bot-`
   - Netlify will auto-detect the settings

3. **Set Environment Variables:**
   ```
   OPENAI_API_KEY=your_openai_key_here
   OPENAI_MODEL=gpt-3.5-turbo
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   ```

4. **Deploy!** 🎉

### Method 2: Netlify CLI

```bash
npm install -g netlify-cli
netlify login
netlify init
netlify deploy --prod
```

## 🔗 Webhook URLs

After deployment, your URLs will be:
- **Voice Webhook:** `https://your-site.netlify.app/voice`
- **Health Check:** `https://your-site.netlify.app/health`

## ⚙️ Twilio Configuration

1. Go to your Twilio Console
2. Navigate to Phone Numbers → Manage → Active numbers
3. Click your phone number
4. Set the webhook URL to: `https://your-site.netlify.app/voice`
5. Set HTTP method to `POST`
6. Save configuration

## ✅ Testing

1. **Health Check:** Visit `https://your-site.netlify.app/`
2. **Voice Test:** Call your Twilio number
3. **Function Logs:** Check Netlify function logs for debugging

## 🔧 Environment Variables Required

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-...` |
| `OPENAI_MODEL` | AI model to use | `gpt-3.5-turbo` |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | `AC...` |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | `...` |

## 🐛 Troubleshooting

- **Build fails:** Check that all dependencies are in `package.json`
- **Functions error:** Check Netlify function logs
- **No response:** Verify environment variables are set
- **Twilio errors:** Check webhook URL and HTTP method

## 📊 Monitoring

- **Netlify Dashboard:** Function invocations and errors
- **Twilio Console:** Call logs and webhook delivery
- **Function Logs:** Real-time debugging information

Your voice bot is now ready for production! 🎉
