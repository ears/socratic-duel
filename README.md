# Socratic Duel
*A multi-agent framework built with Google ADK to stress-test academic theses through structured friction.*

---

## The Problem
Standard LLMs suffer from **consensus bias**. When evaluating complex arguments, they default to generic, middle-of-the-road summaries that lack academic rigor and leave critical blind spots completely unchallenged.

## The Solution
**Socratic Duel** replaces passive agreement with adversarial debate. Instead of blending viewpoints, it forces specialized academic lenses into a structured dialectical conflict to ruthlessly expose flaws, biases, and gaps in a thesis.

---

## How It Works

```
[ Thesis Input ] ➔ [ Lens Selection (1 of 8) ] ➔ [ Protagonist vs. Contrarian Duel ] ➔ [ Synthesis Report ]
```

* **1. Lens Selection:** You provide a thesis. The system presents **8 distinct epistemic lenses** (e.g., *The Empiricist*, *The Systems Theorist*) and recommends the optimal framework for your argument.
* **2. The Adversarial Loop:** A dynamically assigned **Protagonist** and **Contrarian** agent lock into an interactive reflection loop, aggressively debating your thesis from opposing academic strongholds.
* **3. The Synthesis:** A final **Synthesizer** agent distills the clash into a comprehensive, interdisciplinary report—mapping out your argument's methodological integrity alongside its deepest blind spots.


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

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project). *Note: You do not need to install Python manually; `uv` will automatically download and install the correct Python version for you.* 
  - **Linux/macOS**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - **Windows**: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
  - See full [Installation Instructions](https://docs.astral.sh/uv/getting-started/installation/)
- **agents-cli**: Agents CLI - Install with `uv tool install google-agents-cli`
- **Google Cloud SDK**: For GCP services - [Installation Instructions](https://cloud.google.com/sdk/docs/install)

### Authentication Setup

Before running the application, you must configure your environment variables by copying `.env.example` to a new `.env` file in the root directory:

```bash
cp .env.example .env
```

Open `.env` and configure your authentication using one of two methods:

- **Option A: Google Cloud / Vertex AI (Recommended)**
  - Ensure `GOOGLE_GENAI_USE_VERTEXAI=true` is set.
  - Fill in your `GOOGLE_CLOUD_PROJECT`.
  - Authenticate locally by running: `gcloud auth application-default login`
  
- **Option B: Google AI Studio API Key**
  - Comment out the Vertex AI settings in `.env`.
  - Uncomment the `GEMINI_API_KEY` line and paste your API key.


## Quick Start with Make (optional, but convenient)

If you want to automate installation, running both servers simultaneously, and deploying, you can use `make`. 
**Note:** `make` is completely optional. It's built for convenience but requires `make` to be installed on your system.

**Installing `make`:**
- **Windows (Chocolatey):** `choco install make` ([link](https://community.chocolatey.org/packages/make))
- **Windows (GnuWin32):** Download from [SourceForge](http://gnuwin32.sourceforge.net/packages/make.htm) or use `winget install GnuWin32.Make`
- **Linux (Ubuntu/Debian):** `sudo apt install make`
- **macOS:** Built-in, or install via `xcode-select --install`

**Available Make Commands:**
- `make install`: Installs both Python (`uv`) and Node (`npm`) dependencies.
- `make run`: Starts both the backend and frontend simultaneously.
- `make deploy`: Automatically builds and deploys the Socratic Duel app to Google Cloud Run.
- `make undeploy`: Tears down the Google Cloud Run service.

## Quick Start (for the rest of us)

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
uv run uvicorn app.main:app --reload --reload-dir app
```
*(Note: We use `uvicorn` with an explicit `--reload-dir app` flag instead of `fastapi dev` to prevent Windows background tasks from triggering endless hot-reload loops by touching the `.venv` directory).*

2. **Start the React Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Deployment

```bash
gcloud config set project <your-project-id>
agents-cli deploy
```
