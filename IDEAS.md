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
