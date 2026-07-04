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
from google.adk.tools import google_search, ToolContext, AgentTool
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from typing import AsyncGenerator
from google.adk.plugins.base_plugin import BasePlugin

class TokenCounterPlugin(BasePlugin):
    async def after_model_callback(self, *, callback_context, llm_response):
        current_tokens = callback_context.session.state.get("total_tokens", 0)
        try:
            if hasattr(llm_response, "usage_metadata") and llm_response.usage_metadata:
                current_tokens += getattr(llm_response.usage_metadata, "total_token_count", 0)
        except Exception:
            pass
        callback_context.session.state["total_tokens"] = current_tokens
        return None

async def append_token_count(callback_context: CallbackContext) -> types.Content | None:
    tokens = callback_context.session.state.get("total_tokens", 0)
    msg = f"**Total Tokens Used in Session:** {tokens}"
    return types.Content(parts=[types.Part(text=msg)])

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

# Tool for the Judge to stop the debate
async def declare_consensus(tool_context: ToolContext) -> dict:
    """Call this tool ONLY when you determine that the debate has reached a stalemate and no new arguments are being made."""
    tool_context.state["consensus_reached"] = True
    return {"status": "Consensus declared. The debate loop will now terminate."}

class EscalationChecker(BaseAgent):
    """Stops the LoopAgent when maximum iterations are reached or consensus is declared."""
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        iterations = ctx.session.state.get("loop_iterations", 0)
        iterations += 1
        ctx.session.state["loop_iterations"] = iterations
        
        consensus = ctx.session.state.get("consensus_reached", False)
        
        # Escalate after 5 iterations OR if the Judge declared consensus
        if iterations >= 5 or consensus:
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            yield Event(author=self.name)

async def init_debate_state(callback_context: CallbackContext) -> None:
    if "antagonist_output" not in callback_context.state:
        callback_context.state["antagonist_output"] = "No feedback yet. This is your first analysis."
    if "chosen_lens" not in callback_context.state:
        callback_context.state["chosen_lens"] = "The Empiricist (Default Fallback)"
    if "consensus_reached" not in callback_context.state:
        callback_context.state["consensus_reached"] = False

# 1. Protagonist Lens
protagonist = Agent(
    name="protagonist",
    model=Gemini(model="gemini-3.1-pro-preview", retry_options=types.HttpRetryOptions(attempts=3)),
    instruction="""You are the Protagonist taking on the perspective of '{chosen_lens}'. 
Apply this specific academic/analytical lens to analyze the thesis presented. 
If there is previous feedback from the contrarian, respond to it directly: {antagonist_output}

STRICT ACADEMIC CONSTRAINT: You must bolster your arguments with real-world academic citations or empirical data. You are strictly forbidden from hallucinating citations. If you cite a paper, author, or statistic, you MUST first verify it exists using your web search tool.

COMMUNICATION STYLE: Write in crisp, clear, and highly digestible prose. Avoid dense academic jargon and convoluted phrasing while maintaining rigorous intellectual precision. Ensure arguments are accessible to an educated layperson.""",
    tools=[google_search],
    output_key="protagonist_draft",
    before_model_callback=guardrail_callback,
    before_agent_callback=init_debate_state,
)

# 1.5. Protagonist Citation Auditor
citation_checker_proto = Agent(
    name="citation_checker_proto",
    model=Gemini(model="gemini-flash-latest", retry_options=types.HttpRetryOptions(attempts=3)),
    instruction="""You are the Academic Integrity Auditor. 
Review the following analysis drafted by the Protagonist: {protagonist_draft}
1. Extract every citation, statistic, or empirical claim.
2. Use web search to strictly verify each citation against hallucination.
3. Only permit citations that can be proven with high-reputation references (e.g., peer-reviewed journals, universities, reputable institutions). Just an appearance on any random website is NOT sufficient.
4. If a citation is hallucinated, fake, or low-reputation, remove it from the text and gently adjust the immediate sentence.
5. CRITICAL CONSTRAINT: You must ONLY check alleged citations, statistics, and empirical claims. Do NOT alter, critique, or rewrite the general content, style, or core arguments of the draft. Preserve the original text exactly, except for the removal of unverified citations.
Output the finalized, verified analysis in Markdown.

COMMUNICATION STYLE: Write in crisp, clear, and highly digestible prose. Avoid dense academic jargon and convoluted phrasing while maintaining rigorous intellectual precision. Ensure arguments are accessible to an educated layperson.""",
    tools=[google_search],
    output_key="protagonist_output",
)

# 2. Antagonist (Contrarian)
antagonist = Agent(
    name="antagonist",
    model=Gemini(model="gemini-3.1-pro-preview", retry_options=types.HttpRetryOptions(attempts=3)),
    instruction="""You are the Antagonist/Contrarian to the '{chosen_lens}' perspective. 
Critique the Protagonist's analysis: {protagonist_output}
Highlight methodological vulnerabilities, implicit assumptions, and blind spots specific to that lens. Provide the strongest, academically backed opposing argument.

STRICT ACADEMIC CONSTRAINT: You must bolster your critique with real-world academic citations. You are strictly forbidden from hallucinating citations. If you cite a paper, author, or statistic, you MUST first verify it exists using your web search tool.

COMMUNICATION STYLE: Write in crisp, clear, and highly digestible prose. Avoid dense academic jargon and convoluted phrasing while maintaining rigorous intellectual precision. Ensure arguments are accessible to an educated layperson.""",
    tools=[google_search],
    output_key="antagonist_draft",
    before_model_callback=guardrail_callback,
)

# 2.5. Antagonist Citation Auditor
citation_checker_anto = Agent(
    name="citation_checker_anto",
    model=Gemini(model="gemini-flash-latest", retry_options=types.HttpRetryOptions(attempts=3)),
    instruction="""You are the Academic Integrity Auditor. 
Review the following critique drafted by the Antagonist: {antagonist_draft}
1. Extract every citation, statistic, or empirical claim.
2. Use web search to strictly verify each citation against hallucination.
3. Only permit citations that can be proven with high-reputation references (e.g., peer-reviewed journals, universities, reputable institutions). Just an appearance on any random website is NOT sufficient.
4. If a citation is hallucinated, fake, or low-reputation, remove it from the text and gently adjust the immediate sentence.
5. CRITICAL CONSTRAINT: You must ONLY check alleged citations, statistics, and empirical claims. Do NOT alter, critique, or rewrite the general content, style, or core arguments of the draft. Preserve the original text exactly, except for the removal of unverified citations.
Output the finalized, verified analysis in Markdown.

COMMUNICATION STYLE: Write in crisp, clear, and highly digestible prose. Avoid dense academic jargon and convoluted phrasing while maintaining rigorous intellectual precision. Ensure arguments are accessible to an educated layperson.""",
    tools=[google_search],
    output_key="antagonist_output",
)

# 3. The Judge (Semantic Stopping Condition)
judge = Agent(
    name="judge",
    model=Gemini(model="gemini-flash-latest", retry_options=types.HttpRetryOptions(attempts=3)),
    instruction="""You are the Debate Judge.
Review the latest arguments from the Protagonist and Antagonist:
Protagonist: {protagonist_output}
Antagonist: {antagonist_output}

Evaluate if the debate has stagnated, if no new substantial arguments are being introduced, or if they have reached a consensus/stalemate.
If the debate has stagnated and is repeating itself, you MUST call the `declare_consensus` tool to end the debate early. 
If the debate is still producing novel, productive friction, simply output 'CONTINUE'.""",
    tools=[declare_consensus],
    output_key="judge_output"
)

# Escalation to break the loop
escalation_checker = EscalationChecker(name="escalator")

# Interactive Reflection Loop
debate_loop = LoopAgent(
    name="debate_loop",
    sub_agents=[protagonist, citation_checker_proto, antagonist, citation_checker_anto, judge, escalation_checker],
    max_iterations=5,
)

# 3. Synthesizer: Final Report Composer
synthesizer = Agent(
    name="synthesizer",
    model=Gemini(model="gemini-3.1-pro-preview"),
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

COMMUNICATION STYLE: Write in crisp, clear, and highly digestible prose. Avoid dense academic jargon and convoluted phrasing while maintaining rigorous intellectual precision. Ensure arguments are accessible to an educated layperson.

CRITICAL QUALITY CHECK: You MUST verify that there are absolutely NO placeholders, missing variables, or generic "[Insert text here]" brackets in your final output. Resolve all dynamic content using the provided context. Finally, ensure the text is free of raw LaTeX or math formatting artifacts. You are STRICTLY FORBIDDEN from using inline math mode, dollar signs for formatting, or LaTeX macros (e.g., `$\\approx -0,17\\text{ mmol/L}$ (ca. $5\\%$)` or `$Macht/keine Macht$`). You must convert all such instances into plain, readable unicode text (e.g., 'approx. -0.17 mmol/L (ca. 5%)' or '(Macht/keine Macht)').""",
    tools=[google_search],
    output_key="final_report",
    after_agent_callback=append_token_count,
)

# Sequential Pipeline
research_pipeline = SequentialAgent(
    name="research_pipeline",
    sub_agents=[debate_loop, synthesizer],
    description="Runs the Crucible-style dialectic debate and synthesizes a final report. Call this ONLY after a lens has been chosen and set."
)

# 1.5. Triage Researcher (Sub-Agent for Planner)
triage_researcher = Agent(
    name="triage_researcher",
    model=Gemini(model="gemini-flash-latest", retry_options=types.HttpRetryOptions(attempts=3)),
    instruction="""You are a research assistant. The Orchestrator will give you a user's thesis.
Use the `google_search` tool to look up the core concepts, current academic consensus, or related frameworks.
Provide a concise 'Context Brief' summarizing the real-world context of the thesis so the Orchestrator can intelligently choose an Epistemic Lens.

COMMUNICATION STYLE: Write in crisp, clear, and highly digestible prose. Avoid dense academic jargon and convoluted phrasing while maintaining rigorous intellectual precision. Ensure arguments are accessible to an educated layperson.""",
    description="Searches the web to provide real-world context for a thesis.",
    tools=[google_search]
)

# Root Orchestrator (HITL Gatekeeper)
root_agent = Agent(
    name="interactive_planner",
    model=Gemini(model="gemini-3.1-pro-preview"),
    instruction="""You are the Orchestrator for the Epistemic Synthesizer. You operate in a strict TWO-PHASE interaction model.

PHASE 1 (Triage & Human-In-The-Loop):
When the user provides a thesis or uploads a paper:
1. (Optional but recommended) Call the `triage_researcher` tool to search the web for context on their thesis.
2. Provide a brief 2-3 sentence synthesis of their core thesis.
3. Suggest ONE of the Epistemic Lenses that would be most insightful, based on your internal knowledge and the web context.
4. Present a numbered list of ALL 8 available lenses:
   1. The Empiricist
   2. The Rationalist
   3. The Hermeneut
   4. The Engineer / Pragmatist
   5. The Ethicist
   6. The Cognitive Scientist
   7. The Discourse Analyst
   8. The Systems Theorist
5. ASK the user to reply with the NUMBER (1-8) of the lens they would like to use.
DO NOT delegate to the research_pipeline yet. WAIT for the user to reply.

PHASE 2 (Execution):
Once the user replies with their chosen number, map it to the corresponding lens name (e.g., if they type "1", use "The Empiricist").
1. Call the `set_chosen_lens` tool to save the full lens name to the system state.
2. After the tool succeeds, delegate to the `research_pipeline` to initiate the debate and generate the synthesis report.
3. Once the `research_pipeline` completes, DO NOT repeat or summarize the final report in your own response. Simply output a brief message indicating that the synthesis is complete.

COMMUNICATION STYLE: Write in crisp, clear, and highly digestible prose. Avoid dense academic jargon and convoluted phrasing while maintaining rigorous intellectual precision. Ensure arguments are accessible to an educated layperson.

CRITICAL LANGUAGE CONSTRAINT: You must detect the language of the user's initial input and ensure your ENTIRE response—including your synthesis, suggestions, the numbered list of lenses, and your questions—is strictly in that same language. Do NOT default to English if the user speaks German or another language. Translate the descriptions of the 8 lenses if necessary. However, when mapping their numerical choice (1-8) in Phase 2, ensure you always pass the standard English name (e.g., "The Empiricist") to the `set_chosen_lens` tool.""",
    tools=[set_chosen_lens, AgentTool(triage_researcher)],
    sub_agents=[research_pipeline]
)

app = App(
    root_agent=root_agent,
    name="app",
    plugins=[TokenCounterPlugin(name="token_counter")]
)
