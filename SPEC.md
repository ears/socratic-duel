# Epistemic Synthesizer - Specification (MVP)

This document serves as the central "Source of Truth" for the `epistemic-synth` Capstone project. If the project needs to be recreated, refactored, or scaled, this specification acts as the precise blueprint. It captures the architectural decisions, non-functional requirements, and the distinct *intent* behind the design choices.

---

## 1. Purpose & Why

**The Problem:** When standard LLMs are asked to analyze complex theses or arguments, they often produce a generic, middle-of-the-road consensus that lacks academic rigor and fails to expose critical blind spots.
**The Solution:** The "Dialectical Epistemic Synthesizer". Inspired by the Crucible specification, this system avoids generic consensus by actively forcing a dialectical debate between highly specialized academic lenses.
**The Purpose:** The system employs a Human-In-The-Loop (HITL) gatekeeper. The user provides a thesis, and the system suggests an appropriate epistemic lens (e.g., The Empiricist, The Systems Theorist) while listing all 8 available options. Once the user selects a lens, the system pits a dynamically assigned protagonist against a contrarian in an interactive reflection loop. They aggressively stress-test the user's thesis. Only after this loop concludes does a Synthesizer agent combine the arguments into a comprehensive, interdisciplinary report that highlights both methodological integrity and profound blind spots.

---

## 2. The Master Prompt (System Architecture & Workflow)

You are an expert Google ADK developer. Please build the "Epistemic Synthesizer" using the following architecture:

1. Scaffold a new ADK project named `epistemic-synth` using `agents-cli scaffold create epistemic-synth --agent adk --prototype`.
2. Rewrite `app/agent.py` to implement a multi-agent dialectical pipeline.
3. **Human-In-The-Loop (HITL):** Implement a strict Two-Phase interaction model in the root agent. Phase 1: Triage the thesis, suggest a lens, present all 8 lenses (with explicit 1-2 sentence descriptions for each), and wait for the user to select one. Phase 2: Save the user's choice using a custom `set_chosen_lens` tool, then execute the pipeline.
4. **The Crucible Loop:** Implement an interactive reflection loop (`LoopAgent`) that forces a protagonist agent and an antagonist agent to debate the user's input. The antagonist must actively critique the protagonist's previous output. 
5. **Natural Language Communication:** The agents must communicate using raw, unstructured Markdown text rather than strict JSON schemas. This ensures a fluid, high-quality academic debate without wasting tokens on JSON overhead.
6. **Synthesis:** Once the loop terminates, pass the entire debate transcript to a `SequentialAgent` pipeline where a final Synthesizer agent writes the concluding Markdown report.
7. **Built-in Tooling:** Equip the `triage_researcher`, `protagonist`, `antagonist`, `citation_checker`s, and `synthesizer` agents with the `google_search` tool to ensure all analysis, triage, and synthesis are grounded in real-world web data.

---

## 3. Security & Stability Guardrails

The architecture must include robust protections to prevent runaway costs and malicious usage:

1. **Token Explosion Prevention:** The `LoopAgent` must never run indefinitely. Implement an `EscalationChecker` (a custom `BaseAgent`) that acts as a circuit breaker. It must yield an `escalate=True` event either strictly after 5 iterations OR if a semantic Judge agent declares a consensus to terminate the loop early and safely.
2. **Global Cost Tracking:** Implement a custom `TokenCounterPlugin` (inheriting from `BasePlugin`) injected at the `App` level. It must intercept the `after_model_callback` for every agent in the architecture, tally the `usage_metadata.total_token_count`, and store it in session memory. The Synthesizer must use an `after_agent_callback` to extract this tally and append it to the bottom of the final Markdown report.
3. **Prompt Injection Mitigation:** Implement a `before_model_callback` (e.g., `guardrail_callback`) that intercepts every LLM request. If the user attempts to jailbreak the system (e.g., "ignore previous instructions"), the callback must block the request and return a hardcoded security alert, completely bypassing the LLM.
4. **Bring-Your-Own-Key (BYOK):** No hardcoded API keys. The system must rely on `.env` configuration or Google Cloud Application Default Credentials (ADC) for Vertex AI access.

---

## 4. Architectural Logic (Agent Orchestration)

The backend must consist of the following orchestrated ADK components, utilizing a **Hybrid Model Architecture** (`gemini-3.1-pro-preview` for deep reasoning, and `gemini-flash-latest` for simple utility tasks):

- **`triage_researcher`** (Flash): A sub-agent equipped with `google_search` that provides real-world context for a thesis.
- **`interactive_planner` (Root, Pro)**: The overarching orchestrator that enforces the HITL two-phase model. It utilizes an `AgentTool` to delegate initial web research to the `triage_researcher`, interacts with the user to select a lens, and then delegates the workload to the main pipeline.
- **`research_pipeline`**: A `SequentialAgent` that strictly enforces the order of operations:
  1. **`debate_loop`**: A `LoopAgent` that runs the dialectical debate.
      - **`protagonist`** (Pro): Generates the initial epistemic frame using the dynamically injected `{chosen_lens}`.
      - **`citation_checker_proto`** (Flash): An Academic Integrity Auditor that intercepts the protagonist's draft, verifies citations via web search, and removes hallucinations.
      - **`antagonist`** (Pro): Critiques the protagonist from the contrarian perspective of the `{chosen_lens}`.
      - **`citation_checker_anto`** (Flash): An Academic Integrity Auditor that verifies the antagonist's citations via web search.
      - **`judge`** (Flash): A semantic stopping condition agent that reviews the debate and calls the `declare_consensus` tool if arguments stagnate.
      - **`escalator`**: The `BaseAgent` that counts iterations and checks for consensus, stopping the loop at 5 rounds or earlier.
  2. **`synthesizer`** (Pro): Reads the final state of the debate, conducts a web search for overarching concepts, and generates the output report.

---

## 5. Developer Experience (DX) & Non-Functional Requirements (NFR)

1. **State Initialization & Custom Tools:** To prevent "Context variable not found" crashes, the protagonist agent must include a `before_agent_callback` (`init_debate_state`) that injects default placeholders. Custom tools (`set_chosen_lens`, `declare_consensus`) enable agents to write selections and stopping flags directly into state memory.
2. **Standard CLI Testing:** The agent must be fully testable via the standard `agents-cli playground` interface without requiring custom frontend harnesses for the MVP.
3. **Deployment Readiness:** While currently a `--prototype`, the project must maintain a structure compatible with `agents-cli scaffold enhance` for future push-button deployment to Google Cloud Run or Agent Runtime.

---

## 6. Agent Prompt Engineering (Intents & Rules)

The system instructions for the agents in `app/agent.py` must adhere to these strict behavioral rules:

1. **General Communication Style (All Text-Generating Agents):**
   - **Rule:** Must write in crisp, clear, highly digestible prose accessible to an educated layperson, avoiding dense academic jargon while maintaining rigorous intellectual precision.
2. **`interactive_planner` (Root Orchestrator):**
   - **Explicit Lens Descriptions:** Must hardcode and provide brief (1-2 sentence) descriptions for each of the 8 lenses when presenting choices to the user.
   - **Language Constraint:** Must dynamically detect the user's initial input language and ensure its entire response (including lens suggestions and descriptions) is strictly in that same language, preventing fallback to English.
3. **`protagonist` & `antagonist` (Dynamic Debaters):**
   - **Intent:** Must explicitly attack methodological vulnerabilities or defend the epistemic frame based on the `{chosen_lens}`. 
   - **Strict Academic Constraint:** Must bolster arguments with real-world academic citations and are strictly forbidden from hallucinating.
4. **`citation_checker` (Academic Integrity Auditors):**
   - **Intent:** Must extract every citation or empirical claim from the debaters' drafts, verify them against high-reputation references via web search, and explicitly remove any hallucinations or fake sources.
   - **Strict Constraint:** Must ONLY check alleged citations and strictly preserve the original text, core arguments, and author's voice without rewriting or critiquing the draft.
5. **`judge` (The Semantic Referee):**
   - **Intent:** Evaluate if the debate has stagnated or if no new substantial arguments are being introduced. If stagnant, call the `declare_consensus` tool. Otherwise, output 'CONTINUE'.
6. **`synthesizer` (The Final Writer):**
   - **Intent:** Must not merely summarize; must actively use web search to find meta-analyses or interdisciplinary frameworks that resolve the tension.
   - **Rule:** "Zero Placeholders, Maximum Clarity, No Math Formatting." Strictly forbidden from using generic placeholders like `[Insert text here]`. It must execute a "CRITICAL QUALITY CHECK" to ensure clarity, lack of jargon, and explicitly forbid inline math mode (e.g. `$Word$`) to prevent the LLM from outputting raw LaTeX variables.
