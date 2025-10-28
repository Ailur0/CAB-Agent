# 🚀 Quick Start - Teams Integration

Get your AI assistant in Teams in 15 minutes!

---

## ✅ What I Created for You

1. **`src/bot/gemini_integration.py`** - Gemini AI integration
2. **`src/bot/bot.py`** - Updated to use Gemini (already modified)
3. **`TEAMS_SETUP.md`** - Complete setup guide
4. **`start_teams_bot.bat`** - Quick launcher script

---

## 🎯 Quick Setup (15 minutes)

### **1. Install ngrok** (2 min)

```bash
# Download from https://ngrok.com/download
# Or use chocolatey:
choco install ngrok
```

### **2. Create Azure Bot** (5 min)

1. Go to https://portal.azure.com
2. Create resource → "Azure Bot"
3. Name: `change-management-bot-yourname`
4. Pricing: **F0 (Free)**
5. Create new App ID
6. **Copy App ID and Secret!**

### **3. Update .env** (2 min)

Add to your `.env`:
```bash
MICROSOFT_APP_ID=your-app-id-here
MICROSOFT_APP_PASSWORD=your-secret-here
BOT_HOST=0.0.0.0
BOT_PORT=3978
```

### **4. Start ngrok** (1 min)

```bash
ngrok http 3978
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

### **5. Configure Bot** (3 min)

In Azure Portal → Your Bot → Configuration:
- Messaging endpoint: `https://your-ngrok-url.ngrok-free.app/api/messages`
- Click Apply

In Channels:
- Add Microsoft Teams channel
- Click "Open in Teams"

### **6. Start Bot** (2 min)

```bash
# Option 1: Use the launcher
start_teams_bot.bat

# Option 2: Run directly
python src/bot/app.py
```

### **7. Test in Teams!** 🎉

Open Teams → Search for your bot → Start chatting!

---

## 💬 Example Conversations

**Query CRs:**
```
You: Show me 3 change requests from the past week
Bot: [Shows 3 recent CRs with details]
```

**Get Details:**
```
You: Get details for CR2579597
Bot: [Shows full CR information]
```

**Create CR:**
```
You: Create a Normal Change Request for database upgrade 
     scheduled for tomorrow 2pm to 4pm
Bot: [Creates CR and returns ID]
```

**Filter:**
```
You: Show me Draft CRs assigned to me
Bot: [Shows filtered results]
```

---

## 🔧 Troubleshooting

### Bot not responding?

1. **Check ngrok:** Visit http://localhost:4040
2. **Check bot:** Visit http://localhost:3978/health
3. **Check logs:** Look at terminal where bot is running
4. **Check Azure:** Verify messaging endpoint is correct

### Common Issues:

**"401 Unauthorized"**
- Wrong App ID or Password in `.env`

**"404 Not Found"**
- ngrok URL not updated in Azure Portal
- Bot not running

**"Gemini API Error"**
- Check `GOOGLE_API_KEY` in `.env`

**"TFS Connection Error"**
- Check `AZURE_DEVOPS_PAT` in `.env`

---

## 📚 Next Steps

✅ **Working:** Teams chat with Gemini AI + TFS integration

**Want to add:**
- 📧 Email notifications
- 📅 Calendar integration (Graph API)
- 🎨 Adaptive cards for rich UI
- 🔔 Proactive notifications
- 📊 Dashboards and reports

See `TEAMS_SETUP.md` for detailed instructions!

---

## 🎯 Architecture

```
Microsoft Teams
      ↓
Azure Bot Service (via ngrok)
      ↓
Your Bot (app.py)
      ↓
Gemini AI (gemini_integration.py)
      ↓
TFS Tools (query, create, update)
      ↓
RealPage TFS
```

---

## ✨ Features

✅ Natural language understanding
✅ Query TFS change requests
✅ Create new CRs
✅ Update existing CRs
✅ Filter by state, type, date
✅ Conversation history per user
✅ Error handling
✅ Logging

---

## 💡 Tips

- Keep ngrok running while testing
- Each ngrok restart = new URL = update Azure
- Use `start_teams_bot.bat` for easy launching
- Check logs for debugging
- Test with different queries

---

## 🎉 You're Ready!

Follow the 7 steps above and you'll have your AI assistant in Teams!

Questions? Check `TEAMS_SETUP.md` for detailed guide.
