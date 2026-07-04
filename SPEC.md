# Epistemic Synthesizer - Specification (MVP)

This document serves as the central "Source of Truth" for the `epistemic-synth` Capstone project. If the project needs to be recreated, refactored, or scaled, this specification acts as the precise blueprint. It captures the architectural decisions, non-functional requirements, and the distinct *intent* behind the design choices.

---

## 1. Purpose & Why

**The Problem:** When standard LLMs are asked to analyze complex theses or arguments, they often produce a generic, middle-of-the-road consensus that lacks academic rigor and fails to expose critical blind spots.
**The Solution:** The "Dialectical Epistemic Synthesizer". Inspired by the Crucible specification, this system avoids generic consensus by actively forcing a dialectical debate between highly specialized academic lenses.
**The Purpose:** The system pits a protagonist (The Empiricist) against an antagonist (The Contrarian) in an interactive reflection loop. They aggressively stress-test the user's thesis. Only after this loop concludes does a Synthesizer agent combine the arguments into a comprehensive, interdisciplinary report that highlights both methodological integrity and profound blind spots.

---

## 2. The Master Prompt (System Architecture & Workflow)

You are an expert Google ADK developer. Please build the "Epistemic Synthesizer" using the following architecture:

1. Scaffold a new ADK project named `epistemic-synth` using `agents-cli scaffold create epistemic-synth --agent adk --prototype`.
2. Rewrite `app/agent.py` to implement a multi-agent dialectical pipeline.
3. **The Crucible Loop:** Implement an interactive reflection loop (`LoopAgent`) that forces a protagonist agent and an antagonist agent to debate the user's input. The antagonist must actively critique the protagonist's previous output. 
4. **Natural Language Communication:** The agents must communicate using raw, unstructured Markdown text rather than strict JSON schemas. This ensures a fluid, high-quality academic debate without wasting tokens on JSON overhead.
5. **Synthesis:** Once the loop terminates, pass the entire debate transcript to a `SequentialAgent` pipeline where a final Synthesizer agent writes the concluding Markdown report.
6. **Built-in Tooling:** Equip the protagonist agent with the `google_search` tool to ensure empirical claims are grounded in actual web data.

---

## 3. Security & Stability Guardrails

The architecture must include robust protections to prevent runaway costs and malicious usage:

1. **Token Explosion Prevention:** The `LoopAgent` must never run indefinitely. Implement an `EscalationChecker` (a custom `BaseAgent`) that acts as a hard circuit breaker. It must yield an `escalate=True` event strictly after 5 iterations to terminate the loop safely.
2. **Prompt Injection Mitigation:** Implement a `before_model_callback` (e.g., `guardrail_callback`) that intercepts every LLM request. If the user attempts to jailbreak the system (e.g., "ignore previous instructions"), the callback must block the request and return a hardcoded security alert, completely bypassing the LLM.
3. **Bring-Your-Own-Key (BYOK):** No hardcoded API keys. The system must rely on `.env` configuration or Google Cloud Application Default Credentials (ADC) for Vertex AI access.

---

## 4. Architectural Logic (Agent Orchestration)

The backend must consist of the following orchestrated ADK components:

- **`interactive_planner` (Root)**: The overarching orchestrator that receives the initial thesis and delegates the workload to the pipeline.
- **`research_pipeline`**: A `SequentialAgent` that strictly enforces the order of operations:
  1. **`debate_loop`**: A `LoopAgent` that runs the dialectical debate.
      - **`empiricist` (Protagonist)**: Generates the initial empirical frame.
      - **`contrarian` (Antagonist)**: Critiques the empiricist.
      - **`escalator`**: The `BaseAgent` that counts iterations and stops the loop at 5.
  2. **`synthesizer`**: Reads the final state of the debate and generates the output report.

---

## 5. Developer Experience (DX) & Non-Functional Requirements (NFR)

1. **State Initialization:** To prevent "Context variable not found" crashes on the very first loop iteration, the protagonist agent must include a `before_agent_callback` (`init_debate_state`) that injects a default placeholder for the antagonist's output.
2. **Standard CLI Testing:** The agent must be fully testable via the standard `agents-cli playground` interface without requiring custom frontend harnesses for the MVP.
3. **Deployment Readiness:** While currently a `--prototype`, the project must maintain a structure compatible with `agents-cli scaffold enhance` for future push-button deployment to Google Cloud Run or Agent Runtime.

---

## 6. Agent Prompt Engineering (Intents & Rules)

The system instructions for the agents in `app/agent.py` must adhere to these strict behavioral rules:

1. **`empiricist` (The Protagonist):**
   - **Intent:** Must focus solely on empirical evidence, experimental design, and causality. Must respond directly to the Contrarian's previous feedback if it exists in the state.
2. **`contrarian` (The Antagonist):**
   - **Intent:** Must explicitly attack the methodological vulnerabilities and implicit assumptions of the Empiricist's output. Must provide the strongest, academically backed opposing argument.
3. **`synthesizer` (The Final Writer):**
   - **Rule:** "Zero Placeholders, Maximum Clarity."
   - **Intent:** The synthesizer is strictly forbidden from using generic placeholders like `[Insert text here]`. It must execute a "CRITICAL QUALITY CHECK" internally before returning the text, ensuring the final interdisciplinary synthesis is clear, concise, and devoid of obfuscating jargon.
