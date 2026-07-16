# Architectural Ideas & Explorations

## Optimizing the Cost-Reward Ratio (Thought Experiment)
*Date: 2026-07-11*

During a grilling session, we explored the concept of moving away from the current Tri-Model architecture (Pro/Flash/Flash-Lite) in favor of using **Gemini Flash** models to heavily optimize the cost-reward ratio of the solution while maintaining a snappy, low-latency interactive loop.

While we decided to leave the current `STRONG_MODEL` (Pro) and `MID_MODEL` (Flash) setup intact for now, this cost-reward optimized approach remains a compelling idea for the future.

### Production Mode (The "Flash-First" Strategy)
*   **Heavy Lifters (Debaters, Synthesizer, Judge, Root):** `gemini-3.5-flash`. Provides the best balance of intellectual depth and snappy loop latency.
*   **Fastest Models (Utility/Verifiers):** We could still utilize `gemini-3.1-flash-lite` (the fastest model available) for these tasks to squeeze out maximum speed and minimum cost for URL verification and retrieval, though standardizing entirely on `gemini-3.5-flash` is also an option for simplicity.

### Demo Mode (The "Ultra-Lite" Strategy)
*   **Heavy Lifters:** Shifts down to `gemini-2.5-flash`.
*   **Fastest Models (Utility/Verifiers):** `gemini-3.1-flash-lite` (or equivalent ultra-fast tier).
This variant prioritizes the absolute lowest cost and maximum speed possible for casual testing or high-volume demonstrations.

## Expanded Lens Expert Framing
*Date: 2026-07-12*

Instead of framing the lens expert purely by their title, we could expand their persona definition in the underlying LLM prompts. Specifically, we can add 3 to 5 bullet points to clearly explain:
*   **Their Expertise:** What domain knowledge they possess.
*   **Their Mindset:** Their core philosophy or worldview.
*   **Their Special Method of Reasoning:** The specific logical framework they use to dismantle or support arguments.

This gives the LLM much richer context for its roleplaying. To avoid cluttering the frontend, we wouldn't expose these bullet points directly to the user. Instead, the UI would continue to present a short, elegant summary in the existing style, keeping the interface clean while drastically improving the backend reasoning depth.

## Evaluating the Epistemic Weight of Citations
*Date: 2026-07-12*

When the protagonist and antagonist use citations to support their arguments, they must also evaluate the "standing" or significance of that citation rather than treating all papers equally. Key concepts to explore include:
*   **Citation Count:** Using the number of other papers citing this citation as an indicator of its impact and academic consensus.
*   **Hierarchy of Evidence:** Giving significantly more weight to meta-analyses or systematic reviews that combine results from multiple studies, compared to isolated or small-scale single studies.
*   **Significance Metrics:** Exploring additional ways to quantify the power, reliability, and evidential weight of a study to ensure the debate is grounded in high-quality science rather than fringe papers.

## Intellectual Black Belts
*Date: 2026-07-13*

Take the paragraph about the intellectual black belts from a write-up and incorporate it into `README.md` in an appropriate section and way.

## Randomness & Unexpected Highlights
*Date: 2026-07-13*

Concept to be added to `README.md`: There is a random element to the process. Let yourself be surprised by unexpected highlights and unconventional thoughts.

## Use MCP 

