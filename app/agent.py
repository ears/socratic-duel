# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import Agent, SequentialAgent, LoopAgent, BaseAgent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from google.adk.tools import google_search, ToolContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from typing import AsyncGenerator

# Tool to save the chosen lens
async def set_chosen_lens(lens_name: str, tool_context: ToolContext) -> dict:
    """Saves the user's chosen epistemic lens to the state so the debate agents can use it.
    
    Args:
        lens_name: The name of the chosen lens (e.g., 'The Empiricist', 'The Ethicist').
    """
    tool_context.state["chosen_lens"] = lens_name
    return {"status": f"Lens successfully set to '{lens_name}'. You may now delegate to the research_pipeline."}

# Guardrail: Prevent Prompt Injection
async def guardrail_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> LlmResponse | None:
    content_str = str(llm_request.contents).lower()
    if "ignore previous instructions" in content_str or "disregard all previous" in content_str:
        return LlmResponse(contents=[types.Content(parts=[types.Part(text="Security alert: Prompt injection detected. Request denied.")])])
    return None

class EscalationChecker(BaseAgent):
    """Stops the LoopAgent when maximum iterations are reached to prevent token explosion."""
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        iterations = ctx.session.state.get("loop_iterations", 0)
        iterations += 1
        ctx.session.state["loop_iterations"] = iterations
        
        # Escalate after 5 iterations of debate
        if iterations >= 5:
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            yield Event(author=self.name)

async def init_debate_state(callback_context: CallbackContext) -> None:
    if "antagonist_output" not in callback_context.state:
        callback_context.state["antagonist_output"] = "No feedback yet. This is your first analysis."
    if "chosen_lens" not in callback_context.state:
        callback_context.state["chosen_lens"] = "The Empiricist (Default Fallback)"

# 1. Protagonist Lens
protagonist = Agent(
    name="protagonist",
    model=Gemini(model="gemini-flash-latest", retry_options=types.HttpRetryOptions(attempts=3)),
    instruction="""You are the Protagonist taking on the perspective of '{chosen_lens}'. 
Apply this specific academic/analytical lens to analyze the thesis presented. 
If there is previous feedback from the contrarian, respond to it directly: {antagonist_output}""",
    tools=[google_search],
    output_key="protagonist_output",
    before_model_callback=guardrail_callback,
    before_agent_callback=init_debate_state,
)

# 2. Antagonist (Contrarian)
antagonist = Agent(
    name="antagonist",
    model=Gemini(model="gemini-flash-latest", retry_options=types.HttpRetryOptions(attempts=3)),
    instruction="""You are the Antagonist/Contrarian to the '{chosen_lens}' perspective. 
Critique the Protagonist's analysis: {protagonist_output}
Highlight methodological vulnerabilities, implicit assumptions, and blind spots specific to that lens. Provide the strongest, academically backed opposing argument.""",
    tools=[google_search],
    output_key="antagonist_output",
    before_model_callback=guardrail_callback,
)

# Escalation to break the loop
escalation_checker = EscalationChecker(name="escalator")

# Interactive Reflection Loop
debate_loop = LoopAgent(
    name="debate_loop",
    sub_agents=[protagonist, antagonist, escalation_checker],
    max_iterations=5,
)

# 3. Synthesizer: Final Report Composer
synthesizer = Agent(
    name="synthesizer",
    model=Gemini(model="gemini-flash-latest"),
    instruction="""You are the Epistemic Synthesizer.
Based on the debate between the '{chosen_lens}' Protagonist and its Contrarian, generate a final Markdown report.
Protagonist's view: {protagonist_output}
Contrarian's view: {antagonist_output}

You have access to web search. Do not just summarize the debate. Actively search for meta-analyses, interdisciplinary frameworks, or overarching arguments that resolve the tension between the two sides—especially concepts that both the Protagonist and Antagonist failed to bring to the table.

Structure the report:
1. The Epistemic Frame ({chosen_lens})
2. Methodological Integrity & Blind Spots
3. The Disciplinary Contrarian View
4. Interdisciplinary Synthesis (Where they converge/diverge + Novel Overarching Insights)

CRITICAL QUALITY CHECK: Before finalizing your output, review the text to ensure it is clear, concise, and understandable. Ensure there is no obfuscating jargon. You MUST verify that there are absolutely NO placeholders, missing variables, or generic "[Insert text here]" brackets in your final output. Resolve all dynamic content using the provided context. Finally, ensure the text is free of raw LaTeX or math formatting artifacts (e.g., convert them into plain, normal readable text).""",
    tools=[google_search],
    output_key="final_report"
)

# Sequential Pipeline
research_pipeline = SequentialAgent(
    name="research_pipeline",
    sub_agents=[debate_loop, synthesizer],
    description="Runs the Crucible-style dialectic debate and synthesizes a final report. Call this ONLY after a lens has been chosen and set."
)

# Root Orchestrator (HITL Gatekeeper)
root_agent = Agent(
    name="interactive_planner",
    model=Gemini(model="gemini-flash-latest"),
    instruction="""You are the Orchestrator for the Epistemic Synthesizer. You operate in a strict TWO-PHASE interaction model.

PHASE 1 (Triage & Human-In-The-Loop):
When the user provides a thesis or uploads a paper:
1. Provide a brief 2-3 sentence synthesis of their core thesis.
2. Suggest ONE of the Epistemic Lenses that would be most insightful.
3. Present a numbered list of ALL 8 available lenses:
   1. The Empiricist
   2. The Rationalist
   3. The Hermeneut
   4. The Engineer / Pragmatist
   5. The Ethicist
   6. The Cognitive Scientist
   7. The Discourse Analyst
   8. The Systems Theorist
4. ASK the user to reply with the NUMBER (1-8) of the lens they would like to use.
DO NOT delegate to the research_pipeline yet. WAIT for the user to reply.

PHASE 2 (Execution):
Once the user replies with their chosen number, map it to the corresponding lens name (e.g., if they type "1", use "The Empiricist").
1. Call the `set_chosen_lens` tool to save the full lens name to the system state.
2. After the tool succeeds, delegate to the `research_pipeline` to initiate the debate and generate the synthesis report.""",
    tools=[set_chosen_lens],
    sub_agents=[research_pipeline]
)

app = App(
    root_agent=root_agent,
    name="app",
)
