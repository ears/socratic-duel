# Socratic Duel - Specification

This document serves as the central "Source of Truth" for the `socratic-duel` project. If the project needs to be recreated, refactored, or scaled, this specification acts as the precise blueprint. It captures the architectural decisions, non-functional requirements, and the distinct *intent* behind the design choices.

---

## 1. Purpose & Why

**The Problem:** When standard LLMs are asked to analyze complex theses or arguments, they often produce a generic, middle-of-the-road consensus that lacks academic rigor and fails to expose critical blind spots.
**The Solution:** "Socratic Duel". This system avoids generic consensus by actively forcing a rigorous dialectical debate between specialized academic lenses, stress-testing ideas through structured opposition.
**The Purpose:** The system employs a Human-In-The-Loop (HITL) gatekeeper. The user provides a thesis, and the system suggests an appropriate epistemic lens (e.g., The Empiricist, The Systems Theorist) while listing all 8 available options. Once the user selects a lens, the system pits a dynamically assigned protagonist against a contrarian in an interactive reflection loop. They aggressively stress-test the user's thesis. Only after this loop concludes does a Synthesizer agent combine the arguments into a comprehensive, interdisciplinary report that highlights both methodological integrity and profound blind spots.

---

## 2. The Master Prompt (System Architecture & Workflow)

You are an expert Google ADK developer. Please build "Socratic Duel" using the following architecture:

1. Scaffold a new ADK project named `epistemic-synth` using `agents-cli scaffold create epistemic-synth --agent adk --prototype`.
2. Rewrite `app/agent.py` to implement a multi-agent dialectical pipeline.
3. **Human-In-The-Loop (HITL):** Implement a strict Two-Phase interaction model in the root agent. Phase 1 (Input Evaluation & Triage): First, validate the input, strictly blocking prompt injections and gently rejecting non-theses (outputting a `[STATUS: REJECTED]` tag). Then, triage the valid thesis and suggest the single most appropriate lens. (Do not output the other lenses as text; the UI handles this visually). Phase 2: Save the user's choice using a custom `set_chosen_lens` tool, then execute the pipeline.
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

The backend must consist of the following orchestrated ADK components. To optimize reasoning capabilities while maintaining cost-efficiency and a snappy interactive loop, the architecture utilizes a "Flash-First" model approach exclusively in the `global` region via Vertex AI:
- **`STRONG_MODEL`** & **`MID_MODEL`** (`gemini-3.5-flash`): Used by the Root Orchestrator, Debaters, Synthesizer, Semantic Judge, and Triage Researcher. Provides the best balance of intellectual depth and loop latency.
- **`FAST_MODEL`** (`gemini-3.1-flash-lite`): Used by the rapid integrity auditors to squeeze out maximum speed and minimum cost for URL verification.
- **`Demo Mode`**: A feature toggled from the UI ("faster, less costly"). When active, a custom `DynamicGemini` model wrapper cascades the heavy lifters (STRONG and MID models) down to `gemini-2.5-flash` to optimize speed and cost during testing or casual use. The utility/verifiers remain on `gemini-3.1-flash-lite`.

- **Thinking Configuration (`types.ThinkingConfig`) Strategy**:
  - **Debaters (`protagonist`, `antagonist`)**: Moderate-to-high thinking budget to ensure deep, logical arguments in real-time without stalling loop latency.
  - **Evaluators (`synthesizer`)**: High thinking budget. Dictates the final outcome and evaluates the full context, requiring maximum reasoning power.
  - **Judge (`judge`)**: Medium thinking budget. Needs sufficient oversight for loop conditions without bottlenecking the debate loop latency.
  - **Orchestrator (`interactive_planner`)**: Low-to-moderate thinking budget to accurately parse intent and establish the initial debate lens.
  - **Utility / Verifiers (`citation_checker_proto`, `citation_checker_anto`, `triage_researcher`)**: Disabled (Standard generation). Optimized for speed during straightforward retrieval and fact extraction.

- **`triage_researcher`**: A sub-agent equipped with `google_search` that provides real-world context for a thesis.
- **`interactive_planner` (Root)**: The overarching orchestrator that enforces the HITL two-phase model. It utilizes an `AgentTool` to delegate initial web research to the `triage_researcher`, interacts with the user to select a lens, and then delegates the workload to the main pipeline.
- **`research_pipeline`**: A `SequentialAgent` that strictly enforces the order of operations:
  1. **`debate_loop`**: A `LoopAgent` that runs the dialectical debate.
      - **`protagonist`**: Generates the initial epistemic frame using the dynamically injected `{chosen_lens}`.
      - **`citation_checker_proto`**: An Academic Integrity Auditor that intercepts the protagonist's draft, verifies citations via web search, and removes hallucinations.
      - **`antagonist`**: Critiques the protagonist from the contrarian perspective of the `{chosen_lens}`.
      - **`citation_checker_anto`**: An Academic Integrity Auditor that verifies the antagonist's citations via web search.
      - **`judge`**: A semantic stopping condition agent that reviews the debate. It skips the first 2 rounds of the debate (via a pre-execution callback) to let arguments develop. When active, it uses a strict grading rubric (checking for strawmen, empirical gaps, and circular rhetoric) to determine if the debate has stagnated, explicitly keeping feedback short, crisp, and actionable. It must be highly lenient and allow multiple rounds of debate before outputting a structured JSON decision (via `response_schema`) to either continue or end the debate.
      - **`escalator`**: The `BaseAgent` that counts iterations and checks for consensus (by parsing the Judge's structured JSON output), stopping the loop at a hard limit of 5 rounds. If the hard limit is reached, it dynamically injects a final system message into the UI stream *as the Judge*, explaining that the iteration limit was triggered.
  2. **`synthesizer`**: Reads the final state of the debate, conducts a web search for overarching concepts, and generates the output report.

---

## 5. Developer Experience (DX) & Non-Functional Requirements (NFR)

### 5.1 Backend & Architecture
1. **State Initialization & Custom Tools:** To prevent "Context variable not found" crashes, the protagonist agent must include a `before_agent_callback` (`init_debate_state`) that injects default placeholders. Custom tools (`set_chosen_lens`, `declare_consensus`) enable agents to write selections and stopping flags directly into state memory.
2. **Stateful Loop Resumability:** The application uses ADK's `InMemorySessionService` to track transcripts and memory during execution. Because ADK's `LoopAgent` natively restarts the iteration block from the first sub-agent upon resuming from a crash (e.g. an API 503 Overload), custom `before_resume_callback`s must intercept each sub-agent request. By tracking `current_step` in `ctx.session.state`, the backend instantly yields cached drafts for already-executed sub-agents and fast-forwards to the exact agent whose turn it was, ensuring redundant tasks aren't re-run. Furthermore, the `interactive_planner` relies on a `synthesis_complete` flag set ONLY by the `synthesizer`'s `after_agent_callback`. This prevents the planner from hallucinating that synthesis is complete upon resume.
3. **Standard CLI Testing:** The agent must be fully testable via the standard `agents-cli playground` interface.
4. **Deployment Readiness:** While currently a `--prototype`, the project must maintain a structure compatible with `agents-cli scaffold enhance` for future push-button deployment to Google Cloud Run or Agent Runtime.
5. **Hot-Reloading:** The development server must support hot-reloading. Changes to core logic (like swapping `STRONG_MODEL` in `agent.py`) must instantly trigger a backend restart without manual intervention when running via `agents-cli playground` or `uvicorn --reload`.

### 5.2 Frontend & Deployment Specifications
1. **React Frontend with Tailwind CSS v4**: Create a React frontend (using Vite). For styling, strictly use **Tailwind CSS v4** (leveraging zero-config, native CSS nesting, and high performance). Because Tailwind v4 dropped class-based dark mode configuration, `index.css` must explicitly define `@custom-variant dark (&:is(.dark *));` to map `dark:` utility classes to the custom theme toggle.
2. **Cloud-Ready (Single Container Architecture)**: The setup must be deployable as "Serverless" on Google Cloud Run. A multi-stage `Dockerfile` builds the React bundle and injects it into the Python container, which serves both the API and the website on a single port via static mounts (FastAPI).
3. **Design (UI)**: The frontend must offer both "Light" and "Dark" mode with a toggle switch, and must start in "Light Mode" by default. In "Light Mode", bright backgrounds and dark text ensure that the application remains perfectly readable even outdoors in direct sunlight.
4. **Interactive HITL Triage UI (Phase 1)**: The frontend must accurately visually represent the Phase 1 Human-In-The-Loop (HITL) model. Rather than a generic planning UI, it should display the user's initial thesis and present the 8 predefined epistemic lenses as selectable UI cards. Clicking a lens card must instantly select the lens and auto-start the debate pipeline (bypassing an extra "Start Debate" button), though the UI structure should remain open for future multi-lens selection. During the loading phases, a pulsing message ("A little patience, please. Gemini’s gears are turning for you...") must be displayed.
5. **Live Dialectical Debate UI (Phase 2/3)**: During the execution of the debate loop, the frontend must visually display the ongoing back-and-forth arguments. While the models are generating, a dynamic `currentActivity` status update (streamed via SSE `keepalive` events) must be shown under the header with a soft pulse animation to indicate progress. The backend middleware (`main.py`) must aggressively scrub internal tags (like `[STATUS: VERIFIED]` or `[DRAFT:]`) from the raw LLM outputs before they hit the frontend. To maintain UI cleanliness, the frontend must intercept all generated text prior to `ReactMarkdown` rendering and use Regex (`/\$([^\$]+)\$/g`) to silently strip hallucinated raw LaTeX math wrappers (`$ $`) to prevent control character bleeding, and another Regex (`/\s*\[?\d+\]\./g`) to silently strip Gemini Search Grounding artifacts (e.g., `3]. 3].`). Furthermore, hallucinated citations flagged by the Auditors must be formatted and displayed in a distinct red alert box. Valid URLs must render as "Citation Pills".
6. **Synthesis UI (Phase 4)**: The final report generated by the Synthesizer must be visually distinct from the standard debate messages. It must utilize a "Royal Violet" theme (e.g., `bg-violet-50` in Light Mode, `bg-violet-900/20` in Dark Mode) to signify the resolution and conclusion of the dialectical process.
7. **Visual Documentation**: Core concepts must strictly be visualized as Mermaid diagrams (`DIAGRAMS.md`) to enable rapid onboarding for junior developers.
8. **App Reset**: The header logo must be clickable to instantly reset the application to its initial state, allowing the user to easily start a "New Socratic Dialogue".
9. **Connection Resiliency**: The frontend provides a "Resume Connection" button to recover from transient API errors (e.g., 503 Overloads). When clicked, the frontend must first verify the session's existence by querying the backend's history endpoint. If the in-memory session is still active, the debate gracefully resumes without reloading or duplicating previously posted output. If the session has been lost due to server scaling to zero or restarting, the frontend must display a graceful failure message instead of attempting to restart the debate from the beginning.

---

## 6. Agent Prompt Engineering (Intents & Rules)

The system instructions for the agents in `app/agent.py` must adhere to these strict behavioral rules:

1. **General Communication Style (All Text-Generating Agents):**
   - **Rule:** Must write in crisp, clear, highly digestible prose while dynamically adapting its vocabulary, conceptual depth, and tone to the specific `{target_audience}` selected by the user.
   - **Target Audience Profiling:** The UI prepends a `[Target Audience: ...]` tag to the user's initial thesis. The `interactive_planner` parses this tag and saves it to the global state via the `set_chosen_lens` tool. This ensures all downstream agents (Debaters, Auditors, Synthesizer) automatically adapt their complexity to one of 4 defined levels:
     - Level 1 (15-year-old) (This is the default value)
     - Level 2 (Average Adult)
     - Level 3 (Average Academic)
     - Level 4 (PhD-Level)
   - **Persistent Language Tracking:** Every single agent in the `research_pipeline` MUST have `{language}` dynamically injected into its system prompt, accompanied by a `CRITICAL LANGUAGE CONSTRAINT` forcing it to output exclusively in that language to prevent English fallbacks. However, agents MUST be explicitly instructed NOT to translate backend formatting tags (like `[STATUS: ...]`, `---DRAFT---`) so they remain parsable.
2. **`interactive_planner` (Root Orchestrator):**
   - **Phase-Specific Dynamic Prompting:** Instead of a single monolithic prompt handling both phases, it uses a `before_agent_callback` to dynamically inject `{phase_instructions}` based on whether it is in Phase 1 (Triage) or Phase 2 (Execution), ensuring the model remains strictly focused on the current task and preventing phase-confusion.
   - **Input Evaluation Guardrail:** Must evaluate the input before doing anything else. If it's a prompt injection or non-thesis fragment, it must output `[STATUS: REJECTED]` and politely decline, instructing the frontend to halt triage and display the rejection message.
   - **No Redundant Lists:** Must explicitly NOT list the 8 lenses or ask the user to reply in its text output, as the frontend UI handles the presentation and selection of lenses visually.
   - **Language Constraint:** Must dynamically detect the user's initial input language and ensure its entire response is strictly in that same language, preventing fallback to English.
   - **Strict Tool Schema Anchoring:** To prevent `MALFORMED_FUNCTION_CALL` errors, the instruction must explicitly tell the model the exact parameter names for its tools (e.g., pass the thesis as the `'request'` parameter for `triage_researcher`).
   - **State Persistence for Downstream Agents:** Because downstream agents do not natively receive the orchestrator's history, the `set_chosen_lens` tool MUST capture and save the original `{thesis}`, the detected `{language}`, and the dense `{context_summary}` (gathered by the `triage_researcher` in Phase 1) alongside the lens name. This preserves the preliminary research context for the debaters.
   - **Sequential Delegation:** In Phase 2, the prompt must explicitly forbid parallel tool calling. The agent must call `set_chosen_lens`, wait for a success status, and *then* use the delegation tool to transfer control in a subsequent turn. Furthermore, it must be explicitly forbidden from delegating to the `research_pipeline` more than once per session to prevent infinite loop restarts after the final report completes.
3. **`protagonist` & `antagonist` (Dynamic Debaters):**
   - **Intent:** Must explicitly attack methodological vulnerabilities or defend the epistemic frame based on the `{chosen_lens}`. 
   - **LENS ANCHOR Constraint:** To combat context drift over 5 rounds, both debaters are constrained by a `LENS ANCHOR` rule. They are permitted to digress into new domains but MUST explicitly evaluate them through their specific epistemic lens. They must also synthesize a "Thesis Statement" explaining how their major points derive from their assigned philosophy.
   - **Role Constraint:** Must strictly maintain their initial positions and never switch sides or argue from the opposing perspective, avoiding generic consensus seeking entirely.
   - **XML Boundary Guardrails:** The opponent's dynamically injected previous output (`{antagonist_output}`), the Judge's feedback (`{judge_output}`), the Phase 1 research context (`{context_summary}`), and the rolling debate memory (`{full_transcript}`) MUST be wrapped in strict XML boundary tags (`<CONTRARIAN_FEEDBACK>`, `<PROTAGONIST_ANALYSIS>`, `<JUDGE_FEEDBACK>`, `<PHASE_1_RESEARCH>`, `<DEBATE_HISTORY>`) in the prompt. Since `include_contents="none"` forces the model to rely purely on instructions for history, these XML barriers prevent the model from confusing the injected variable with its own identity instructions. The debaters are explicitly instructed that they MUST correct any logical flaws pointed out by the Judge. Furthermore, injecting the `{full_transcript}` prevents "Amnesia," ensuring debaters maintain a coherent working memory of their own past arguments across all 5 rounds.
   - **Strict Academic URL Constraint:** Must heavily incentivize backing up arguments with real-world academic sources, which MUST be formatted exclusively as Markdown URLs (hyperlinks). Text-only citations are forbidden. Must explicitly be forbidden from citing Wikipedia, Goodreads, or commercial bookstores to ensure high academic rigor. They MUST use the custom `search_semantic_scholar` tool to search for and read real peer-reviewed papers BEFORE drafting their responses to strictly prevent URL hallucinations.
   - **Strict Formatting Constraint:** Must strictly avoid raw LaTeX or math formatting artifacts (e.g., inline `$Word$` formatting) to ensure text remains perfectly readable without requiring frontend math rendering.
4. **`citation_checker` (Academic Integrity Auditors):**
   - **Intent:** Must scan the text exclusively for URLs. If no URLs exist, instantly declare `[STATUS: NO_CITATIONS]`. If URLs exist, strictly verify them via web search and the custom `verify_url_status` tool. They must enforce three rules: (1) The URL is not dead or hallucinated. The `verify_url_status` tool actively pings the URL and parses the `Content-Type`. It returns the HTML `<title>` or explicitly detects `application/pdf` (to prevent false positive "Not Found" errors for PDFs). If a known academic domain returns 403 or 401 (Bot Protection), it must preserve the URL but explicitly append `[🛡️ Bot Protected]` next to the link to transparently inform the user. (2) The URL points to a legitimate academic/journalistic source (strictly rejecting Goodreads, Wikipedia, commercial sites, etc.). (3) Content Congruence (the URL's actual content must empirically support the claim). The `verify_url_status` tool actively extracts and returns the first 1,500 characters of the document (using BeautifulSoup for HTML and PyPDF for PDFs) so the Auditor can actively read the abstract/intro to guarantee empirical congruence. If the URL is Bot Protected (403/401), the auditor MUST bypass the content congruence check and assume validity. The model generation config must explicitly set `temperature=0.1` to maximize analytical precision and prevent formatting hallucinations.
   - **Strict Constraint:** Must strictly preserve the original text, core arguments, and author's voice without rewriting or critiquing the draft.
   - **Formatting & Tag Extraction:** The citation checker must separate its verification status from the finalized text using a bulletproof `---DRAFT---` separator (replacing the legacy `[DRAFT:]` wrapper) to prevent accidental bracket stripping. The backend (`main.py`) must use a robust, language-agnostic Regex (`r"---.*?---"`) to gracefully extract the text even if the model hallucinates a translated tag.
5. **`judge` (The Semantic Referee):**
   - **Intent:** Evaluate if the debate has stagnated. It must skip early rounds and evaluate strictly against a defined grading rubric (strawmen, gaps, circularity). Must output its decision using a strict Pydantic JSON schema (`JudgeDecision`) returning `decision`, `reasoning`, and `audience_feedback`. To prevent rambling, the Pydantic field descriptions strictly enforce a maximum 21-word limit and a "ruthless, surgical, clinical tone" for the reasoning. This brutally honest feedback is injected directly into the debaters' next-round prompts (`<JUDGE_FEEDBACK>`), forcing them to self-correct in real-time. Furthermore, an `after_agent_callback` MUST automatically append the Judge's ruling directly to the `{full_transcript}` so the final Synthesizer agent can factor the Judge's verdict into its concluding report.
   - **Round Escalation:** When the maximum number of rounds is reached, a dedicated pre-judge checking agent must intercept the loop and yield a final hardcoded comment to conclude the debate, skipping the judge's LLM generation entirely to prevent further requests to the duellers.
6. **`synthesizer` (The Final Writer):**
   - **Intent:** Must not merely summarize; must actively use the `search_semantic_scholar` tool and web search to find real peer-reviewed meta-analyses or interdisciplinary frameworks that resolve the tension. It must explicitly begin the report with a large two-line Markdown header without emojis in the first line: `# Socratic Synthesis` followed by `### Through the Lens of: {chosen_lens_icon} {chosen_lens}`.
   - **Language Constraint:** Must output the entire final report (including section headers) in the dynamically injected `{language}`. Do NOT default to English.
   - **Rule:** "Zero Placeholders, Maximum Clarity, No Math Formatting." Strictly forbidden from using generic placeholders like `[Insert text here]`. It must explicitly forbid inline math mode (e.g. `$Word$`) to prevent the LLM from outputting raw LaTeX variables.
   - **Glossary Requirement:** Must explicitly include a "5. Glossary (Abbreviations & Key Terms)" section at the end of the report to define any acronyms or abbreviations used throughout the synthesis.
