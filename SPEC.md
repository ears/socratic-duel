# Socratic Duel - Specification

This document serves as the central "Source of Truth" for the `epistemic-synth` Capstone project. If the project needs to be recreated, refactored, or scaled, this specification acts as the precise blueprint. It captures the architectural decisions, non-functional requirements, and the distinct *intent* behind the design choices.

---

## 1. Purpose & Why

**The Problem:** When standard LLMs are asked to analyze complex theses or arguments, they often produce a generic, middle-of-the-road consensus that lacks academic rigor and fails to expose critical blind spots.
**The Solution:** "Socratic Duel" (formerly the Dialectical Epistemic Synthesizer). This system avoids generic consensus by actively forcing a rigorous dialectical debate between highly specialized academic lenses, stress-testing ideas through structured opposition.
**The Purpose:** The system employs a Human-In-The-Loop (HITL) gatekeeper. The user provides a thesis, and the system suggests an appropriate epistemic lens (e.g., The Empiricist, The Systems Theorist) while listing all 8 available options. Once the user selects a lens, the system pits a dynamically assigned protagonist against a contrarian in an interactive reflection loop. They aggressively stress-test the user's thesis. Only after this loop concludes does a Synthesizer agent combine the arguments into a comprehensive, interdisciplinary report that highlights both methodological integrity and profound blind spots.

---

## 2. The Master Prompt (System Architecture & Workflow)

You are an expert Google ADK developer. Please build "Socratic Duel" using the following architecture:

1. Scaffold a new ADK project named `epistemic-synth` using `agents-cli scaffold create epistemic-synth --agent adk --prototype`.
2. Rewrite `app/agent.py` to implement a multi-agent dialectical pipeline.
3. **Human-In-The-Loop (HITL):** Implement a strict Two-Phase interaction model in the root agent. Phase 1: Triage the thesis, suggest a lens, present all 8 lenses (with explicit 1-2 sentence descriptions for each), and wait for the user to select one. Phase 2: Save the user's choice using a custom `set_chosen_lens` tool, then execute the pipeline.
4. **The Dialectical Debate Loop:** Implement an interactive reflection loop (`LoopAgent`) that forces a protagonist agent and an antagonist agent to debate the user's input. The antagonist must actively critique the protagonist's previous output. 
5. **Natural Language Communication:** The agents must communicate using raw, unstructured Markdown text rather than strict JSON schemas. This ensures a fluid, high-quality academic debate without wasting tokens on JSON overhead.
6. **Synthesis:** Once the loop terminates, pass the entire debate transcript to a `SequentialAgent` pipeline where a final Synthesizer agent writes the concluding Markdown report.
7. **Built-in Tooling:** Equip the `triage_researcher`, `protagonist`, `antagonist`, `citation_checker`s, and `synthesizer` agents with the `google_search` tool to ensure all analysis, triage, and synthesis are grounded in real-world web data.

---

## 3. Security & Stability Guardrails

The architecture must include robust protections to prevent runaway costs and malicious usage:

1. **Token Explosion Prevention:** The `LoopAgent` must never run indefinitely. Implement an `EscalationChecker` (a custom `BaseAgent`) that acts as a circuit breaker. It must yield an `escalate=True` event either strictly after 5 iterations OR if a semantic Judge agent declares a consensus to terminate the loop early and safely.
   - **Context Tracking:** To prevent the massive raw JSON history of web searches from bloating the context window exponentially, all agents within the `research_pipeline` (debaters, checkers, synthesizer) MUST set `include_contents='none'`. They will rely exclusively on dynamic state injection (e.g., `{thesis}`, `{language}`) for historical context.
2. **Global Cost Tracking:** Implement a custom `TokenCounterPlugin` (inheriting from `BasePlugin`) injected at the `App` level. It must intercept the `after_model_callback` for every agent in the architecture, tally the `usage_metadata.total_token_count`, and store it in session memory. The Synthesizer must use an `after_agent_callback` to extract this tally and append it to the bottom of the final Markdown report.
3. **Prompt Injection Mitigation:** Implement a `before_model_callback` (e.g., `guardrail_callback`) that intercepts every LLM request. If the user attempts to jailbreak the system (e.g., "ignore previous instructions"), the callback must block the request and return a hardcoded security alert, completely bypassing the LLM.
4. **Network & API Stability:** To prevent deadlocks when an agent chains too many searches, all models must implement strict API timeouts (`HttpOptions(timeout=60000)`) and cap Automatic Function Calling (AFC) at a maximum of 3 remote calls per turn via `GenerateContentConfig`.
5. **Bring-Your-Own-Key (BYOK):** No hardcoded API keys. The system must rely on `.env` configuration or Google Cloud Application Default Credentials (ADC) for Vertex AI access.

---

## 4. Architectural Logic (Agent Orchestration)

The backend must consist of the following orchestrated ADK components. Due to API region availability constraints, all agents utilize **`gemini-3.1-flash-lite`** in the `global` region (rather than a Pro/Flash split):

- **`triage_researcher`**: A sub-agent equipped with `google_search` that provides real-world context for a thesis.
- **`interactive_planner` (Root)**: The overarching orchestrator that enforces the HITL two-phase model. It utilizes an `AgentTool` to delegate initial web research to the `triage_researcher`, interacts with the user to select a lens, and then delegates the workload to the main pipeline.
- **`research_pipeline`**: A `SequentialAgent` that strictly enforces the order of operations:
  1. **`debate_loop`**: A `LoopAgent` that runs the dialectical debate.
      - **`protagonist`**: Generates the initial epistemic frame using the dynamically injected `{chosen_lens}`.
      - **`citation_checker_proto`**: An Academic Integrity Auditor that intercepts the protagonist's draft, verifies citations via web search, and removes hallucinations.
      - **`antagonist`**: Critiques the protagonist from the contrarian perspective of the `{chosen_lens}`.
      - **`citation_checker_anto`**: An Academic Integrity Auditor that verifies the antagonist's citations via web search.
      - **`judge`**: A semantic stopping condition agent that reviews the debate. It is explicitly instructed to be highly lenient and allow multiple rounds of debate before calling the `declare_consensus` tool or outputting `[DECISION: END]`.
      - **`escalator`**: The `BaseAgent` that counts iterations and checks for consensus, stopping the loop at a hard limit of 5 rounds. If the hard limit is reached, it dynamically injects a final system message into the UI stream *as the Judge*, explaining that the iteration limit was triggered.
  2. **`synthesizer`**: Reads the final state of the debate, conducts a web search for overarching concepts, and generates the output report.

---

## 5. Developer Experience (DX) & Non-Functional Requirements (NFR)

### 5.1 Backend & Architecture
1. **State Initialization & Custom Tools:** To prevent "Context variable not found" crashes, the protagonist agent must include a `before_agent_callback` (`init_debate_state`) that injects default placeholders. Custom tools (`set_chosen_lens`, `declare_consensus`) enable agents to write selections and stopping flags directly into state memory.
2. **Standard CLI Testing:** The agent must be fully testable via the standard `agents-cli playground` interface.
3. **Deployment Readiness:** While currently a `--prototype`, the project must maintain a structure compatible with `agents-cli scaffold enhance` for future push-button deployment to Google Cloud Run or Agent Runtime.

### 5.2 Frontend & Deployment Specifications
1. **React Frontend with Tailwind CSS v4**: Create a React frontend (using Vite). For styling, strictly use **Tailwind CSS v4** (leveraging zero-config, native CSS nesting, and high performance). Because Tailwind v4 dropped class-based dark mode configuration, `index.css` must explicitly define `@custom-variant dark (&:is(.dark *));` to map `dark:` utility classes to the custom theme toggle.
2. **Cloud-Ready (Single Container Architecture)**: The setup must be deployable as "Serverless" on Google Cloud Run. A multi-stage `Dockerfile` builds the React bundle and injects it into the Python container, which serves both the API and the website on a single port via static mounts (FastAPI).
3. **Design (UI)**: The frontend must offer both "Light" and "Dark" mode with a toggle switch, and must start in "Light Mode" by default. In "Light Mode", bright backgrounds and dark text ensure that the application remains perfectly readable even outdoors in direct sunlight.
4. **Interactive HITL Triage UI (Phase 1)**: The frontend must accurately visually represent the Phase 1 Human-In-The-Loop (HITL) model. Rather than a generic planning UI, it should display the user's initial thesis, present the 8 proposed epistemic lenses (with descriptions) generated by the triage agent as selectable UI cards, and explicitly capture the user's choice before initiating the main debate pipeline.
5. **Live Dialectical Debate UI (Phase 2/3)**: During the execution of the debate loop, the frontend must visually display the ongoing back-and-forth arguments. The backend middleware (`main.py`) must aggressively scrub internal tags (like `[STATUS: VERIFIED]` or `[DRAFT:]`) from the raw LLM outputs before they hit the frontend. Furthermore, hallucinated citations flagged by the Academic Integrity Auditors must be formatted and displayed in a distinct red alert box, explicitly attributed to the "CITATION CHECKER". All valid Markdown URLs must render as "Citation Pills" (rounded badges).
6. **Synthesis UI (Phase 4)**: The final report generated by the Synthesizer must be visually distinct from the standard debate messages. It must utilize a "Royal Violet" theme (e.g., `bg-violet-50` in Light Mode, `bg-violet-900/20` in Dark Mode) to signify the resolution and conclusion of the dialectical process.
7. **Visual Documentation**: Core concepts must strictly be visualized as Mermaid diagrams (`DIAGRAMS.md`) to enable rapid onboarding for junior developers.

---

## 6. Agent Prompt Engineering (Intents & Rules)

The system instructions for the agents in `app/agent.py` must adhere to these strict behavioral rules:

1. **General Communication Style (All Text-Generating Agents):**
   - **Rule:** Must write in crisp, clear, highly digestible prose accessible to an educated layperson, avoiding dense academic jargon while maintaining rigorous intellectual precision.
   - **Persistent Language Tracking:** Every single agent in the `research_pipeline` MUST have `{language}` dynamically injected into its system prompt, accompanied by a `CRITICAL LANGUAGE CONSTRAINT` forcing it to output exclusively in that language to prevent English fallbacks.
2. **`interactive_planner` (Root Orchestrator):**
   - **Explicit Lens Descriptions:** Must hardcode and provide brief (1-2 sentence) descriptions for each of the 8 lenses when presenting choices to the user.
   - **Language Constraint:** Must dynamically detect the user's initial input language and ensure its entire response (including lens suggestions and descriptions) is strictly in that same language, preventing fallback to English.
   - **Strict Tool Schema Anchoring:** To prevent `MALFORMED_FUNCTION_CALL` errors (especially when users upload files), the instruction must explicitly tell the model the exact parameter names for its tools (e.g., pass the thesis as the `'request'` parameter for `triage_researcher`, and `'lens_name'` for `set_chosen_lens`).
   - **State Persistence for Downstream Agents:** Because downstream agents do not receive conversational history, `set_chosen_lens` MUST capture and save the original `{thesis}` and the detected `{language}` alongside the lens name.
   - **Sequential Delegation:** In Phase 2, the prompt must explicitly forbid parallel tool calling. The agent must call `set_chosen_lens`, wait for a success status, and *then* use the delegation tool to transfer control in a subsequent turn.
3. **`protagonist` & `antagonist` (Dynamic Debaters):**
   - **Intent:** Must explicitly attack methodological vulnerabilities or defend the epistemic frame based on the `{chosen_lens}`. 
   - **Strict Academic URL Constraint:** Must heavily incentivize backing up arguments with real-world academic sources, which MUST be formatted exclusively as Markdown URLs (hyperlinks). Text-only citations are forbidden.
4. **`citation_checker` (Academic Integrity Auditors):**
   - **Intent:** Must scan the text exclusively for URLs. If no URLs exist, instantly declare `[STATUS: NO_CITATIONS]`. If URLs exist, verify them via web search to strip out dead or hallucinated links.
   - **Strict Constraint:** Must strictly preserve the original text, core arguments, and author's voice without rewriting or critiquing the draft.
5. **`judge` (The Semantic Referee):**
   - **Intent:** Evaluate if the debate has stagnated. Must begin its output strictly with an English machine-readable tag (`[DECISION: CONTINUE]` or `[DECISION: END]`) before explaining its reasoning in the user's `{language}`, guaranteeing robustness in multi-lingual debates.
6. **`synthesizer` (The Final Writer):**
   - **Intent:** Must not merely summarize; must actively use web search to find meta-analyses or interdisciplinary frameworks that resolve the tension.
   - **Language Constraint:** Must output the entire final report (including section headers) in the dynamically injected `{language}`. Do NOT default to English.
   - **Rule:** "Zero Placeholders, Maximum Clarity, No Math Formatting." Strictly forbidden from using generic placeholders like `[Insert text here]`. It must execute a "CRITICAL - **`ensure clarity, lack of`** jargon, offer and explicitly forbid inline math mode (e.g. `$Word$`) to prevent the LLM from outputting raw LaTeX variables.


