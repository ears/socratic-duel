# Socratic Duel (Dialectical Epistemic Synthesizer)

A multi-agent system designed to rigorously analyze theses using highly specialized academic lenses. Built with Google ADK for the AI Agents Intensive Vibe Coding Capstone Project.

See the formal architecture and rule blueprint in [SPEC.md](file:///home/hartmut/scientific-synthesizer/epistemic-synth/SPEC.md).

## Features
- **Human-In-The-Loop Triage**: An orchestrator agent that triages the thesis (aided by a dedicated web-searching `triage_researcher` sub-agent) and lets you dynamically choose from 8 epistemic lenses (e.g., The Systems Theorist, The Ethicist).
- **Dynamic Language Support**: The Orchestrator automatically detects the language of your initial input and conducts the entire session (including lens translations) in that language.
- **Dialectical Debate Loop**: A strictly controlled `LoopAgent` that pits a dynamically assigned protagonist against a contrarian to stress-test your thesis.
- **Academic Integrity Auditors**: Dedicated fact-checking agents that intercept both the protagonist's and antagonist's drafts, using web search to strictly verify the content congruence and academic rigor of every citation while preserving the original debate text.
- **Semantic Debate Judge**: An intelligent referee agent that evaluates the debate and dynamically stops the loop early if arguments stagnate.
- **Interdisciplinary Synthesis**: A final Report Composer agent that actively uses web search to find novel meta-arguments and outputs a clear, zero-placeholder Markdown report.
- **Global Token Tracking**: A custom App-level ADK plugin automatically tallies token usage across all agents (debaters, auditors, judge) and displays the total session cost at the end of the report.
- **Security Guardrails**: Includes a `before_model_callback` to actively block prompt injections.

## Project Structure

```
epistemic-synth/
├── app/         # Core agent code
│   ├── agent.py               # Main agent logic
│   ├── fast_api_app.py        # FastAPI Backend server
│   └── app_utils/             # App utilities and helpers
├── tests/                     # Unit, integration, and load tests
├── GEMINI.md                  # AI-assisted development guide
└── pyproject.toml             # Project dependencies
```

> 💡 **Tip:** Use [Antigravity CLI](https://antigravity.google/) for AI-assisted development - project context is pre-configured in `GEMINI.md`.

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project) - [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **agents-cli**: Agents CLI - Install with `uv tool install google-agents-cli`
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)


## Quick Start

Install `agents-cli` and its skills if not already installed:

```bash
uvx google-agents-cli setup
```

Install required packages:

```bash
agents-cli install
```

Test the agent with a local web server:

```bash
agents-cli playground
```

You can also use features from the [ADK](https://adk.dev/) CLI with `uv run adk`.

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
