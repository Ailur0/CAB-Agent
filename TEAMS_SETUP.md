# Microsoft Teams Integration Setup

Complete guide to get your Change Management AI Assistant running in Microsoft Teams.

---

## 📋 Prerequisites

- ✅ Azure account (free tier works)
- ✅ Microsoft 365 / Teams account
- ✅ Python 3.9+ installed
- ✅ ngrok installed
- ✅ Your existing TFS and Gemini API credentials

---

## 🚀 Step-by-Step Setup

### **Step 1: Register Bot in Azure Portal**

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **"Create a resource"** → Search for **"Azure Bot"**
3. Click **"Create"**

**Configuration:**
- **Bot handle:** `change-management-bot-yourname` (must be globally unique)
- **Subscription:** Your Azure subscription
- **Resource group:** Create new: `rg-change-management`
- **Pricing tier:** **F0 (Free)** - 10,000 messages/month
- **Microsoft App ID:** Click **"Create new"**
- **App type:** **Multi Tenant**

4. Click **"Review + Create"** → **"Create"**

5. **IMPORTANT:** After creation, go to the resource and click **"Configuration"**
   - Copy the **Microsoft App ID** (save this!)
   - Click **"Manage Password"** → **"New client secret"**
   - Copy the **secret value** (you can only see this once!)

---

### **Step 2: Update .env File**

Add these to your `.env` file:

```bash
# Microsoft Teams Bot
MICROSOFT_APP_ID=paste-your-app-id-here
MICROSOFT_APP_PASSWORD=paste-your-secret-here

# Bot Configuration
BOT_HOST=0.0.0.0
BOT_PORT=3978

# Google Gemini (you already have this)
GOOGLE_API_KEY=your-existing-gemini-key

# Azure DevOps / TFS (you already have this)
AZURE_DEVOPS_ORG=realpage
AZURE_DEVOPS_PROJECT=Change_Management
AZURE_DEVOPS_PAT=your-existing-pat
```

---

### **Step 3: Install Required Packages**

```bash
# Install Teams bot dependencies
pip install botbuilder-core botbuilder-schema aiohttp

# Verify all packages
pip list | grep -i bot
```

---

### **Step 4: Start ngrok**

```bash
# Run ngrok on port 3978
ngrok http 3978
```

**Copy the HTTPS URL** from ngrok output:
```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:3978
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            Copy this URL!
```

---

### **Step 5: Configure Bot Messaging Endpoint**

1. Go back to Azure Portal → Your Bot Resource
2. Click **"Configuration"** (left menu)
3. Set **Messaging endpoint:** `https://your-ngrok-url.ngrok-free.app/api/messages`
   - Example: `https://abc123.ngrok-free.app/api/messages`
4. Click **"Apply"**

---

### **Step 6: Add Teams Channel**

1. In Azure Portal → Your Bot → **"Channels"** (left menu)
2. Click the **Microsoft Teams** icon
3. Click **"Save"**
4. Click **"Open in Teams"** to test

---

### **Step 7: Start Your Bot**

```bash
# In your project directory
python src/bot/app.py
```

You should see:
```
🤖 Change Management Bot Starting...
   Host: 0.0.0.0
   Port: 3978
   Endpoints:
      - POST /api/messages (Bot Framework)
      - POST /api/notify (Proactive notifications)
      - GET  /health (Health check)
```

---

### **Step 8: Test in Teams**

1. Click **"Open in Teams"** from Azure Portal
2. Or search for your bot in Teams: `change-management-bot-yourname`
3. Start a conversation!

**Try these:**
- "Hello"
- "Show me 3 change requests"
- "Get details for CR2579597"
- "Show me Draft CRs from the past week"
- "Create a new change request for database upgrade"

---

## 🎯 What Works Now

✅ **Natural language chat** with Gemini AI in Teams
✅ **Query TFS** change requests
✅ **Get CR details** by ID
✅ **Create new CRs** from Teams
✅ **Update existing CRs**
✅ **Filter by state, type, date range**
✅ **Conversation history** per user

---

## 🔧 Troubleshooting

### **Bot not responding in Teams**

1. Check ngrok is running: `http://localhost:4040` (ngrok dashboard)
2. Verify bot is running: `curl http://localhost:3978/health`
3. Check Azure Portal → Bot → Configuration → Messaging endpoint is correct
4. Look at bot logs for errors

### **"401 Unauthorized" errors**

- Verify `MICROSOFT_APP_ID` and `MICROSOFT_APP_PASSWORD` in `.env` are correct
- Make sure you copied the secret VALUE, not the secret ID

### **Gemini AI errors**

- Verify `GOOGLE_API_KEY` is set in `.env`
- Check quota: https://makersuite.google.com

### **TFS connection errors**

- Verify `AZURE_DEVOPS_PAT` is valid
- Check PAT has `Work Items (Read, Write)` permissions

---

## 📱 Deploy to Production (Optional)

For production use (not localhost):

1. **Deploy bot to Azure App Service**
   ```bash
   # Create App Service
   az webapp create --resource-group rg-change-management \
     --plan myAppServicePlan --name my-change-bot --runtime "PYTHON:3.9"
   
   # Deploy code
   az webapp up --name my-change-bot
   ```

2. **Update Messaging Endpoint**
   - Change from ngrok URL to: `https://my-change-bot.azurewebsites.net/api/messages`

3. **Set Environment Variables** in Azure App Service
   - Go to App Service → Configuration → Application settings
   - Add all your `.env` variables

---

## 🎉 You're Done!

Your Change Management AI Assistant is now live in Teams!

**Next Steps:**
- Add more team members to test
- Customize the bot's responses
- Add adaptive cards for richer UI
- Set up proactive notifications

---

## 📚 Additional Resources

- [Bot Framework Documentation](https://docs.microsoft.com/en-us/azure/bot-service/)
- [Teams Bot Samples](https://github.com/microsoft/BotBuilder-Samples)
- [Gemini API Docs](https://ai.google.dev/docs)
- [Azure DevOps REST API](https://docs.microsoft.com/en-us/rest/api/azure/devops/)
