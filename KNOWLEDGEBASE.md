# Socratic Duel - Knowledge Base & Technical Learnings

This document serves as a living record of architectural decisions, technical gotchas, and framework patterns learned while building the **Socratic Duel** Agent Platform application.

## 1. Google ADK & Agent Framework Mechanics
* **Callback State Manipulation:** Callbacks (e.g., `after_agent_callback`) are incredibly powerful for injecting state mid-flight. When modifying responses or generating custom UI events via callbacks, you **must** yield a valid `types.Content(role="model", parts=[...])` structure so the ADK engine can correctly track, render, and append the text to the event stream. 
* **Handling Loop Resumes (The Fast-Forward Pattern):** By default, ADK's `LoopAgent` restarts its execution from the *first* sub-agent if the frontend connection drops and resumes. To fix this, you must track the `current_step` in `ctx.session.state` and use `before_resume_callback` blocks on each sub-agent to instantly yield cached data and fast-forward to the correct agent.
* **Hard Enforcement of Debate Limits:** Instead of relying entirely on LLM reasoning to end a loop, use a `BaseAgent` acting as a circuit-breaker (e.g., `EscalationChecker`) that checks the `iteration` count and forcefully yields `EventActions(escalate=True)`.

## 2. Model Tiering & Cost-Optimization (Flash-First)
* **The `DynamicGemini` Pattern:** By overriding the standard Model class, you can create dynamic routing architectures. We implemented a "Demo Mode" toggle that intercepts the backend stream and automatically downgrades heavy-lifter models from `gemini-3.5-flash` to `gemini-2.5-flash`, saving ~76% in API costs.
* **Pinning Utility Tasks:** Agents that perform rigid, narrow tasks (like the `citation_checker` or URL pinging) do not need frontier models. Pinning them to `gemini-3.1-flash-lite` provides instant latency and drastically cuts costs without sacrificing quality.

## 3. Infrastructure & Statelessness
* **Rethinking Databases:** We successfully migrated away from a heavy Cloud SQL/PostgreSQL database to a lightweight, ephemeral `InMemorySessionService`. This stateless approach:
  1. Completely eliminated the need for complex Terraform provisioning (`google-agents-cli infra single-project`).
  2. Drastically simplified the `Makefile` and `gcloud run deploy` workflows.
  3. Made the app cheaper and faster to host.
* **The Frontend as the Source of Truth:** With an ephemeral backend, the React frontend relies on `EventSource` streams to update its own local history. When the connection drops, it simply restarts the ADK orchestrator from its exact location, passing the cached history without needing to query a persistent database.

## 4. Prompt Engineering & Data Scrubbing
* **Aggressive UI Hygiene:** LLMs will inevitably hallucinate internal artifacts.
  * **LaTeX & Math Tags:** We implemented frontend Regex (`/\$([^\$]+)\$/g`) to strip out unrendered dollar signs and LaTeX artifacts.
  * **Search Grounding Arrays:** We added Regex (`/\s*\[?\d+\]\./g`) to silently strip Gemini Search Grounding references (e.g., `3]. 3].`).
  * **Bulletproof Separators:** When an LLM generates internal JSON/Tags alongside UI text, use robust separators like `---DRAFT---` instead of legacy brackets `[DRAFT:]`, as models are highly prone to misformatting brackets during translation.

## 5. Security & Tooling Quirks
* **Academic Bot Walls:** Real academic portals (JSTOR, Nature, ScienceDirect) use brutal bot-protection firewalls. If a URL Validation tool hits a `403` or `401` error, the app must gracefully assume the URL *might* be alive, appending a UI shield (`[🛡️]`) instead of blindly deleting it.
* **Global Token Tracking:** A custom ADK `AgentPlugin` can hook into every single API call across an entire multi-agent orchestration tree to tally exact Input/Output tokens, which is critical for measuring cost per session.
