# Socratic Duel (Dialectical Epistemic Synthesizer)

A multi-agent system designed to rigorously analyze theses using highly specialized academic lenses. Built with Google ADK for the AI Agents Intensive Vibe Coding Project.

See the formal architecture and rule blueprint in [SPEC.md](file:///home/hartmut/scientific-synthesizer/epistemic-synth/SPEC.md).

## Features
- **Human-In-The-Loop Triage**: An orchestrator agent that triages the thesis (aided by a dedicated web-searching `triage_researcher` sub-agent) and lets you dynamically choose from 8 epistemic lenses (e.g., The Systems Theorist, The Ethicist).
- **Dynamic Language Support**: The Orchestrator automatically detects the language of your initial input and conducts the entire session (including lens translations) in that language.
- **Dialectical Debate Loop**: A strictly controlled `LoopAgent` that pits a dynamically assigned protagonist against a contrarian to stress-test your thesis. They are also strictly constrained from outputting raw LaTeX math formatting to ensure seamless frontend rendering.
- **Academic Integrity Auditors**: Dedicated fact-checking agents that intercept both the protagonist's and antagonist's drafts, using web search to strictly verify the content congruence and academic rigor of every citation while preserving the original debate text. Any links shielded by bot protection are visibly tagged inline so you know exactly where they occur.
- **Semantic Debate Judge**: An intelligent referee agent that skips early rounds to let arguments naturally develop, then evaluates the debate against a rigorous rubric and dynamically stops the loop early if arguments stagnate.
- **Interdisciplinary Synthesis**: A final Report Composer agent that actively uses web search to find novel meta-arguments and outputs a clear, zero-placeholder Markdown report complete with a comprehensive Glossary of all abbreviations used.
- **Global Token Tracking**: A custom App-level ADK plugin automatically tallies token usage across all agents (debaters, auditors, judge) and displays the total session cost at the end of the report.
- **Security Guardrails**: Includes a `before_model_callback` to actively block prompt injections.

## Project Structure

```
epistemic-synth/
├── app/                       # Core Python backend
│   ├── agent.py               # Main agent logic & prompts
│   ├── fast_api_app.py        # FastAPI server entrypoint
│   ├── main.py                # App routing & middleware logic
│   └── app_utils/             # App utilities and helpers
├── frontend/                  # React + Vite frontend UI
├── tests/                     # Unit, integration, and load tests
├── SPEC.md                    # Formal architecture & agent rules
├── ROADMAP.md                 # Project roadmap and milestones
├── DIAGRAMS.md                # System architecture visual diagrams
├── GEMINI.md                  # AI-assisted development guide
├── Dockerfile                 # Multi-stage container deployment
└── pyproject.toml             # Python project dependencies
```

> 💡 **Tip:** Use [Antigravity CLI](https://antigravity.google/) for AI-assisted development - project context is pre-configured in `GEMINI.md`.

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project). *Note: You do not need to install Python manually; `uv` will automatically download and install the correct Python version for you.* 
  - **Linux/macOS**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - **Windows**: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
  - See full [Installation Instructions](https://docs.astral.sh/uv/getting-started/installation/)
- **agents-cli**: Agents CLI - Install with `uv tool install google-agents-cli`
- **Google Cloud SDK**: For GCP services - [Installation Instructions](https://cloud.google.com/sdk/docs/install)


## Quick Start

Install `agents-cli` and its skills if not already installed:

```bash
uvx google-agents-cli setup
```

Install required packages:

```bash
agents-cli install
```

Test the agent with a local webserver (raw agent only, no UI):

```bash
agents-cli playground
```

### Running the Full Application (Backend + Frontend)

1. **Start the FastAPI Backend:**
```bash
uv run uvicorn app.main:app --reload --reload-exclude ".venv"
```
*(Note: We use `uvicorn` with an explicit exclude flag instead of `fastapi dev` to prevent Windows background tasks from triggering endless hot-reload loops by touching the `.venv` directory).*

2. **Start the React Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Using the Core ADK CLI

Because this project is built on the Google Agent Development Kit (ADK), you have full access to the underlying `adk` CLI. This allows you to bypass the `agents-cli` wrapper for advanced debugging or database management.

Run it using `uv` to ensure it executes in the correct virtual environment:
```bash
uv run adk --help
```
*Useful commands include:*
- `uv run adk run app/agent.py`: Run the agent directly from the command line without the web server.
- `uv run adk db clear`: Clear the local SQLite database (`app/.adk/session.db`—where ADK automatically saves all conversation history and agent state) if your session gets corrupted or you want a completely fresh start.

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `agents-cli install` | Install dependencies using uv                                                         |
| `agents-cli playground` | Launch local development environment                                                  |
| `agents-cli lint`    | Run code quality checks                                                               |
| `agents-cli eval`    | Evaluate agent behavior (generate, grade, analyze, and more — see `agents-cli eval --help`) |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests                                                        || [A2A Inspector](https://github.com/a2aproject/a2a-inspector) | Launch A2A Protocol Inspector                                                        |

## 🛠️ Project Management

| Command | What It Does |
|---------|--------------|
| `agents-cli scaffold enhance` | Add CI/CD pipelines and Terraform infrastructure |
| `agents-cli infra cicd` | One-command setup of entire CI/CD pipeline + infrastructure |
| `agents-cli scaffold upgrade` | Auto-upgrade to latest version while preserving customizations |

---

## Development

Edit your agent logic in `app/agent.py` and test with `agents-cli playground` - it auto-reloads on save.

## Deployment

```bash
gcloud config set project <your-project-id>
agents-cli deploy
```

To add CI/CD and Terraform, run `agents-cli scaffold enhance`.
To set up your production infrastructure, run `agents-cli infra cicd`.

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging.

## A2A Inspector

This agent supports the [A2A Protocol](https://a2a-protocol.org/). Use the [A2A Inspector](https://github.com/a2aproject/a2a-inspector) to test interoperability.
See the [A2A Inspector docs](https://github.com/a2aproject/a2a-inspector) for details.
