# Query Examples - AI Assistant

Complete guide to querying change requests using natural language.

---

## 🔍 Query by Assignee

### **By Email:**
```
"Show me CRs assigned to john.doe@realpage.com"
"Get all change requests for jane.smith@realpage.com"
"What CRs are assigned to bob.jones@realpage.com?"
```

### **By Name:**
```
"Show me John Doe's change requests"
"Get all CRs assigned to Jane Smith"
"What change requests does Bob Jones have?"
```

### **Combined with State:**
```
"Show me Active CRs assigned to john.doe@realpage.com"
"Get In Progress items for Jane Smith"
"Show me Draft CRs assigned to bob.jones@realpage.com"
```

### **Combined with Date:**
```
"Show me CRs assigned to john.doe@realpage.com from last week"
"Get Jane Smith's change requests from past 3 days"
"Show me Bob's CRs from the past month"
```

---

## 📊 Query by State

### **Single State:**
```
"Show me all Active change requests"
"Get Pending Approvals"
"List all Draft CRs"
"Show me In Progress items"
"Get all Awaiting PIR change requests"
```

### **Multiple Filters:**
```
"Show me Active Normal Change Requests"
"Get Pending Approvals from last week"
"Show me 5 Draft CRs assigned to me"
```

---

## 📅 Query by Date Range

### **Relative Dates:**
```
"Show me CRs from the past 2 days"
"Get change requests from last week"
"Show me items from the past month"
"Get CRs from the past 7 days"
```

### **Combined with Other Filters:**
```
"Show me Active CRs from past 3 days"
"Get Pending Approvals from last week assigned to john.doe@realpage.com"
"Show me In Progress Normal CRs from past 2 days"
```

---

## 🏷️ Query by Type

### **By Change Type:**
```
"Show me Normal Change Requests"
"Get all Emergency Change Requests"
"List Standard Change Requests"
```

### **Combined Queries:**
```
"Show me Active Emergency CRs"
"Get Pending Approvals for Normal Change Requests"
"Show me In Progress Emergency CRs from last week"
```

---

## 🎯 Complex Queries

### **All Filters Combined:**
```
"Show me 5 Active Normal Change Requests assigned to john.doe@realpage.com from the past week"

"Get 10 In Progress Emergency CRs assigned to Jane Smith from the past 3 days"

"Show me Pending Approvals Standard Change Requests assigned to bob.jones@realpage.com from last month"
```

### **Multiple States:**
```
"Show me CRs in Draft or In Progress state"
"Get all Pending Approvals or Pending CAB items"
```

---

## 📝 Available Filters

| Filter | Parameter | Example Values |
|--------|-----------|----------------|
| **State** | `state` | Active, Draft, In Progress, Pending Approvals, Approved, Closed, etc. |
| **Assignee** | `assigned_to` | john.doe@realpage.com, "John Doe" |
| **Type** | `work_item_types` | Normal Change Request, Emergency Change Request, Standard Change Request |
| **Date** | `days_back` | 2, 7, 30 (days) |
| **Limit** | `limit` | 2, 5, 10 (number of results) |

---

## 🤖 Natural Language Understanding

The AI understands variations:

### **Assignee Variations:**
- "assigned to john.doe@realpage.com"
- "for john.doe@realpage.com"
- "John Doe's CRs"
- "belonging to Jane Smith"
- "owned by Bob Jones"

### **State Variations:**
- "in Draft state"
- "Draft CRs"
- "items in Draft"
- "Draft status"

### **Date Variations:**
- "from the past 2 days"
- "from last week"
- "in the last 7 days"
- "from past month"

---

## 💡 Tips

### **Be Specific:**
✅ "Show me 5 Active CRs assigned to john.doe@realpage.com from past week"
❌ "Show me some stuff"

### **Use Email for Assignee:**
✅ "assigned to john.doe@realpage.com"
⚠️ "assigned to John" (might match multiple people)

### **Limit Results:**
✅ "Show me 5 CRs" (faster, cleaner)
❌ "Show me all CRs" (might be too many)

### **Combine Filters:**
✅ "Active Emergency CRs from last week"
✅ "Draft items assigned to me"

---

## 🚀 Try These Now!

### **CLI Test:**
```bash
python test_agent_direct.py
```

Then try:
```
"Show me 3 CRs assigned to john.doe@realpage.com"
"Get Active items for Jane Smith from past week"
"Show me all Pending Approvals assigned to bob.jones@realpage.com"
```

### **Teams:**
Once your bot is running:
```
"What CRs are assigned to me?"
"Show me John's Active change requests"
"Get all Pending Approvals for jane.smith@realpage.com"
```

---

## 📊 All Available States

- Active
- Approved
- Assigned
- Awaiting PIR
- Cancelled
- Draft
- In Progress
- Pending Approvals
- Pending CAB
- Pending Closure
- Rejected
- Validate
- Closed

---

## ✅ What's Supported

✅ Filter by assignee (email or name)
✅ Filter by state (all 13 states)
✅ Filter by work item type
✅ Filter by date range (days back)
✅ Limit number of results
✅ Combine all filters together
✅ Natural language variations

---

## 🎉 Examples by Use Case

### **Daily Standup:**
```
"Show me my Active CRs"
"What In Progress items do I have?"
"Show me my change requests from this week"
```

### **Team Review:**
```
"Show me all Pending Approvals"
"Get all Awaiting PIR items"
"Show me Pending CAB change requests"
```

### **Manager View:**
```
"Show me all Active CRs for my team"
"Get In Progress Emergency CRs"
"Show me all Pending Approvals from last week"
```

### **Personal Tracking:**
```
"Show me my Draft CRs"
"What CRs am I assigned to?"
"Show me my change requests from past month"
```

---

The AI understands natural language - just ask! 🤖
