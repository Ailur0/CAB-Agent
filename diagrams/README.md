# CAB Agent - Architecture Diagrams

## 📁 Diagram Files

All diagrams are in **Mermaid format** (`.mmd` files) ready for https://mermaidchart.com

| File | Description | Type |
|------|-------------|------|
| `01-system-architecture.mmd` | Complete system architecture with all components | Flowchart |
| `02-proactive-notification-workflow.mmd` | How proactive notifications work | Sequence |
| `03-user-query-workflow.mmd` | User query processing flow | Sequence |
| `04-system-phases.mmd` | Implementation phases (1-5) | Flowchart |
| `05-data-flow.mmd` | Data flow through the system | Flowchart |
| `06-database-schema.mmd` | Database tables and relationships | ER Diagram |
| `07-technology-stack.mmd` | Technology stack overview | Graph |
| `08-combined-architecture-workflow.mmd` | Combined architecture + workflow | Flowchart |

---

## 🎨 How to Use with MermaidChart.com

### Method 1: Import Files Directly

1. Go to https://mermaidchart.com
2. Sign in (free account)
3. Click **"New Diagram"**
4. Click **"Import"** → **"From File"**
5. Select any `.mmd` file from this folder
6. Edit and export as PNG/SVG/PDF

### Method 2: Copy & Paste

1. Open any `.mmd` file in VS Code
2. Copy all content
3. Go to https://mermaidchart.com
4. Click **"New Diagram"**
5. Paste the code
6. Diagram renders automatically!

---

## 🖼️ Viewing Diagrams

### Option 1: MermaidChart.com (Recommended)
- **Best for:** Professional editing and export
- **Features:** 
  - Visual editor
  - Export to PNG, SVG, PDF
  - Share links
  - Themes and styling

### Option 2: VS Code
1. Install extension: **"Markdown Preview Mermaid Support"**
2. Create a `.md` file
3. Wrap diagram code in:
   ````markdown
   ```mermaid
   [paste diagram code here]
   ```
   ````
4. Press `Ctrl+Shift+V` to preview

### Option 3: Mermaid Live Editor
- Go to: https://mermaid.live/
- Paste diagram code
- Export as PNG/SVG

---

## 📊 Diagram Descriptions

### 1. System Architecture (`01-system-architecture.mmd`)
**Shows:**
- All system components
- External systems (Azure DevOps, Teams, Graph API)
- Data layer (SQL Server tables)
- Service layer (Polling, Event Processor)
- Bot layer (Teams Bot, State Manager)
- AI layer (OpenAI)
- Tools layer (Azure DevOps Tools, Notifications)

**Use for:** Understanding overall system structure

---

### 2. Proactive Notification Workflow (`02-proactive-notification-workflow.mmd`)
**Shows:**
- Polling service fetching CRs every 5 minutes
- Change detection logic
- Event rule matching
- Notification sending process
- Database interactions

**Use for:** Understanding how proactive notifications work

---

### 3. User Query Workflow (`03-user-query-workflow.mmd`)
**Shows:**
- User sends message to bot
- Conversation reference storage
- OpenAI processing
- Function calling
- Database vs API queries
- Response formatting

**Use for:** Understanding reactive (user-initiated) flow

---

### 4. System Phases (`04-system-phases.mmd`)
**Shows:**
- Phase 1: Initial Setup (Database)
- Phase 2: Data Population (Sync)
- Phase 3: Background Polling
- Phase 4: Teams Bot Configuration
- Phase 5: Proactive Notifications

**Use for:** Implementation roadmap

---

### 5. Data Flow (`05-data-flow.mmd`)
**Shows:**
- Three main flows: User Query, Background Sync, Notifications
- Decision points
- Database operations
- Error handling

**Use for:** Understanding data movement

---

### 6. Database Schema (`06-database-schema.mmd`)
**Shows:**
- All 4 database tables
- Columns and data types
- Primary keys (PK)
- Foreign keys (FK)
- Relationships

**Use for:** Database design and queries

---

### 7. Technology Stack (`07-technology-stack.mmd`)
**Shows:**
- Frontend: Microsoft Teams
- Backend: Python frameworks
- Database: SQL Server
- External APIs: Azure DevOps, Graph API
- Connections between components

**Use for:** Technology overview

---

### 8. Combined Architecture + Workflow (`08-combined-architecture-workflow.mmd`)
**Shows:**
- Complete system in one diagram
- Both reactive and proactive workflows
- Numbered data flow steps
- All major components

**Use for:** Presentations, documentation, overview

---

## 🎨 Customizing Diagrams

### Change Colors
```mermaid
style ComponentName fill:#HexColor,stroke:#fff,stroke-width:2px,color:#fff
```

### Common Colors:
- Blue: `#326CE5` (Database)
- Green: `#10A37F` (AI/OpenAI)
- Purple: `#5B5FC7` (Teams/Bot)
- Red: `#FF6B6B` (Polling)
- Orange: `#FFA500` (Events)

### Add Components
```mermaid
NewComponent[Component Name<br/>Description]
```

### Add Connections
```mermaid
A -->|Label| B
A -.->|Dotted| B
A ==>|Bold| B
```

---

## 📤 Exporting Diagrams

### From MermaidChart.com:
1. Open diagram
2. Click **"Export"**
3. Choose format:
   - **PNG** - For presentations, documents
   - **SVG** - For websites, scalable graphics
   - **PDF** - For printing, reports

### Recommended Sizes:
- **Presentation:** 1920x1080 (PNG)
- **Documentation:** SVG (scalable)
- **Print:** PDF (high quality)

---

## 🔗 Useful Links

- **MermaidChart.com:** https://mermaidchart.com
- **Mermaid Live Editor:** https://mermaid.live/
- **Mermaid Documentation:** https://mermaid.js.org/
- **Mermaid Syntax Guide:** https://mermaid.js.org/intro/

---

## 💡 Tips

1. **Start with combined diagram** (`08-combined-architecture-workflow.mmd`) for overview
2. **Use sequence diagrams** (`02`, `03`) to explain workflows
3. **Use ER diagram** (`06`) for database discussions
4. **Customize colors** to match your company branding
5. **Export as SVG** for best quality in documents

---

## 🆘 Troubleshooting

### Diagram doesn't render?
- Check for syntax errors (missing brackets, quotes)
- Ensure proper indentation in subgraphs
- Verify all connections have valid node names

### Want to edit visually?
- Use MermaidChart.com's visual editor
- Drag and drop components
- Click to edit text

### Need help?
- Mermaid documentation: https://mermaid.js.org/
- MermaidChart tutorials: https://www.mermaidchart.com/blog

---

## 📝 Next Steps

1. Open any `.mmd` file in MermaidChart.com
2. Customize colors and text for your needs
3. Export as PNG/SVG for presentations
4. Share with your team!
