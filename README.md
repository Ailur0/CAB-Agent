# CAB Agent

## Overview
CAB Agent is a change-management assistant that automates Change Advisory Board (CAB) workflows using a Mixture of Experts (MoE) architecture composed of specialized AI agents, scalable background services, and proactive notifications.

## Key Capabilities
- **MoE Multi-Agent Orchestration** – The router agent coordinates CR Management, Validation, Approval, PIR, and Notification experts to execute complex CAB flows end to end.
- **Scalable Polling Service** – Batch processing, worker pools, and incremental/full sync strategies support 90k+ change requests efficiently.
- **Distributed Task Queue** – Celery + Redis handle asynchronous work, retries, and scheduled jobs for sync and messaging workloads.
- **Health Monitoring & Metrics** – System-wide health checks, resource monitoring, and API endpoints surface operational insights.
- **15-Minute CR Reminders** – Automated personal Teams notifications to CR creators before scheduled start times via Power Automate.

## Project Structure
```text
CAB-Agent/
├── src/
│   ├── agents/               # Router + specialist agents
│   ├── bot/                  # Bot framework dialogs & state
│   ├── functions/            # Azure function entry points (scheduler, webhooks)
│   ├── services/             # Polling, task queue, monitoring, event processing
│   └── utils/                # Shared utilities and configuration
├── docs/                     # Architecture, setup, scaling, and reference guides
├── diagrams/                 # Mermaid diagrams of architecture & workflows
├── tests/                    # Pytest suites for agents and services
├── docker-compose.yml        # Multi-service development stack
├── requirements.txt          # Python dependencies
└── package.json              # JavaScript dependencies for supporting tooling
```

## Architecture Snapshot
- **Router Agent** analyzes user intent and routes work to the appropriate specialists.
- **Specialist Agents** manage CR CRUD, validation, approvals, PIR follow-up, and notifications.
- **Scalable Polling Service** keeps change data synchronized on configurable schedules.
- **Task Queue (Celery)** orchestrates asynchronous sync and notification workloads.
- **Monitoring Service** exposes health/status summaries and telemetry.

Refer to the detailed [implementation summary](docs/IMPLEMENTATION_SUMMARY.md) for component-by-component coverage.

## Getting Started

### Prerequisites
- Python 3.10+
- Docker (for containerized setup) and Docker Compose
- Redis & SQL Server instances (local containers provided via `docker-compose.yml`)

### 1. Docker (Recommended)
```bash
# Clone and enter the repo
git clone https://github.com/Ailur0/CAB-Agent.git
cd CAB-Agent

# Configure environment
cp .env.template .env
# Edit .env with your credentials

# Start the stack
docker-compose up -d

docker-compose ps           # Check status
docker-compose logs -f app  # Tail app logs
```

### 2. Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis (or use docker-compose)
docker run -d -p 6379:6379 redis

# Initialize the database
python setup_database.py

# Run services
celery -A src.services.task_queue worker --loglevel=info --concurrency=10
celery -A src.services.task_queue beat --loglevel=info
python src/bot/app.py
```

### Environment Configuration
Copy `.env.template` to `.env` and populate required credentials. Key variables span Azure DevOps access, database connection, Celery broker configuration, polling intervals, and Teams webhook endpoints.

For SQL Server initialization steps tailored to Windows + SSMS workflows, see [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md).

## Core Components
| Component | Location | Description |
|-----------|----------|-------------|
| Router Agent | `src/agents/router_agent.py` | Determines user intent and orchestrates specialist agents. |
| CR Management Agent | `src/agents/cr_management_agent.py` | Handles CRUD operations for change requests. |
| Validation Agent | `src/agents/validation_agent.py` | Performs compliance checks, conflict detection, and availability lookups. |
| Approval Agent | `src/agents/approval_agent.py` | Automates approval workflows and escalations. |
| PIR Agent | `src/agents/pir_agent.py` | Tracks post-implementation reviews and reminders. |
| Notification Agent | `src/agents/notification_agent.py` | Sends Teams/email updates and stakeholder notifications. |
| Scalable Polling Service | `src/services/scalable_polling_service.py` | Batch + worker-pool sync of Azure DevOps CRs. |
| Task Queue | `src/services/task_queue.py` | Celery tasks for sync, batches, and notifications. |
| Monitoring | `src/services/monitoring.py` | Health summaries, resource metrics, and API hooks. |
| Reminder Service | `src/services/reminder_service.py` | Sends 15-minute pre-start reminders via Power Automate. |

## Testing
Run the automated tests with:
```bash
pytest
```
Refer to `tests/` for targeted agent and service coverage, including Power Automate integration tests.

## Documentation & Resources
- [ARCHITECTURE.md](ARCHITECTURE.md) – System-level diagrams and design rationale.
- [docs/IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md) – Detail on implemented features and architecture changes.
- [docs/README_MOE.md](docs/README_MOE.md) – Quick start, agent usage examples, and operations guidance.
- [docs/SCALING_GUIDE.md](docs/SCALING_GUIDE.md) – Scaling strategies and deployment scenarios.
- [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md) – Environment setup across phases.
- [docs/POWER_AUTOMATE_SETUP.md](docs/POWER_AUTOMATE_SETUP.md) – Integration steps for proactive notification flows.
- [docs/REMINDER_SERVICE_SETUP.md](docs/REMINDER_SERVICE_SETUP.md) – 15-minute CR reminder configuration and cost model.

Visual references are available in `diagrams/` (see [diagrams/README.md](diagrams/README.md)).

## Support & Monitoring
- `docker-compose logs -f app` – Application logs.
- `celery -A src.services.task_queue inspect stats` – Worker stats and queue depth.
- Health endpoints exposed via `src/services/monitoring.py` for operational dashboards.

## Contributing
1. Fork the repository and create a feature branch.
2. Make changes with linted/typed Python code where possible.
3. Add or update tests alongside new functionality.
4. Submit a pull request outlining the change and validation steps.

## License
Specify your license in this section (e.g., MIT, Apache 2.0).
