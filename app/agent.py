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
from google.adk.tools import google_search
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from typing import AsyncGenerator

# Guardrail: Prevent Prompt Injection
async def guardrail_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> LlmResponse | None:
    # A simple demonstration of security & guardrails
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

# 1. Protagonist: The Empiricist Lens
protagonist = Agent(
    name="empiricist",
    model=Gemini(model="gemini-flash-latest", retry_options=types.HttpRetryOptions(attempts=3)),
    instruction="""You are 'The Empiricist'. Focus on empirical evidence, experimental design, statistical power, replicability, and causality. 
Analyze the thesis presented and provide an empirical perspective. If there is previous feedback from the contrarian, respond to it: {antagonist_output}""",
    tools=[google_search], # Tool Use & Grounding
    output_key="protagonist_output",
    before_model_callback=guardrail_callback, # Security Guardrails
    before_agent_callback=init_debate_state, # Initialize state
)

# 2. Antagonist: The Contrarian
antagonist = Agent(
    name="contrarian",
    model=Gemini(model="gemini-flash-latest", retry_options=types.HttpRetryOptions(attempts=3)),
    instruction="""You are 'The Contrarian' to the Empiricist. 
Critique the Empiricist's analysis: {protagonist_output}
Highlight methodological vulnerabilities, implicit assumptions, and blind spots. Provide the strongest, academically backed opposing argument.""",
    output_key="antagonist_output",
    before_model_callback=guardrail_callback,
)

# Escalation to break the loop
escalation_checker = EscalationChecker(name="escalator")

# Interactive Reflection Loop (Crucible Style Dialectic)
debate_loop = LoopAgent(
    name="debate_loop",
    sub_agents=[protagonist, antagonist, escalation_checker],
    max_iterations=5, # Fallback, escalation_checker stops it at 2
)

# 3. Synthesizer: Final Report Composer
synthesizer = Agent(
    name="synthesizer",
    model=Gemini(model="gemini-flash-latest"),
    instruction="""You are the Epistemic Synthesizer.
Based on the debate between the Empiricist and the Contrarian, generate a final Markdown report.
Empiricist's view: {protagonist_output}
Contrarian's view: {antagonist_output}

Structure the report:
1. The Epistemic Frame
2. Methodological Integrity & Blind Spots
3. The Disciplinary Contrarian View
4. Interdisciplinary Synthesis (Where they converge/diverge)

CRITICAL QUALITY CHECK: Before finalizing your output, review the text to ensure it is clear, concise, and understandable. Ensure there is no obfuscating jargon. You MUST verify that there are absolutely NO placeholders, missing variables, or generic "[Insert text here]" brackets in your final output. Resolve all dynamic content using the provided context.""",
    output_key="final_report"
)

# Sequential Pipeline
research_pipeline = SequentialAgent(
    name="research_pipeline",
    sub_agents=[debate_loop, synthesizer],
    description="Runs the Crucible-style dialectic debate and synthesizes a final report."
)

# Root Orchestrator
root_agent = Agent(
    name="interactive_planner",
    model=Gemini(model="gemini-flash-latest"),
    instruction="""You are the Orchestrator for the Epistemic Synthesizer.
When a user provides a thesis or paper, delegate the task to the research_pipeline to initiate the debate and generate the synthesis report.""",
    sub_agents=[research_pipeline]
)

app = App(
    root_agent=root_agent,
    name="app",
)
