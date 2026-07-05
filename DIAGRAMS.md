# Socratic Duel - Architecture & Workflows

## 1. High-Level Triage & Debate Pipeline

This diagram shows the end-to-end flow from the user's initial input to the final synthesized report, highlighting the Human-in-the-Loop (HITL) step.

```mermaid
graph TD
    User(["User Input: Thesis"]) --> Orchestrator["Interactive Planner (Root)"]
    Orchestrator -->|Delegates Context| TriageResearcher[Triage Researcher]
    TriageResearcher -->|Web Search & Context| Orchestrator
    Orchestrator -->|Presents 8 Lenses| UI[HITL: User selects Lens]
    UI -->|Choice 1-8| Orchestrator
    Orchestrator -->|Routes Task| Pipeline[Research Pipeline]
    
    subgraph Pipeline [Sequential Pipeline]
        direction TB
        DebateLoop[Dialectical Debate Loop]
        Synthesizer[Synthesizer]
        
        DebateLoop -->|Final Debate Transcript| Synthesizer
    end
    
    Synthesizer -->|Outputs Markdown| FinalReport(["Final Interdisciplinary Report"])
```

## 2. Dialectical Debate Loop (The Engine)

This diagram details the internal mechanics of the `LoopAgent`.

```mermaid
graph TD
    Start((Loop Start)) --> Protagonist
    
    subgraph Protagonist Block
        Protagonist[Protagonist] -->|Drafts Argument| CheckerP[Citation Checker]
        CheckerP -->|Audits URLs| CheckedP[Verified Protagonist Argument]
    end
    
    CheckedP --> Antagonist
    
    subgraph Antagonist Block
        Antagonist[Antagonist] -->|Critiques Argument| CheckerA[Citation Checker]
        CheckerA -->|Audits URLs| CheckedA[Verified Antagonist Critique]
    end
    
    CheckedA --> Judge{Semantic Judge}
    
    Judge -->|Rounds < 2| Continue1[Sleep / Continue]
    Judge -->|Rounds >= 2 & Active Debate| Continue2[DECISION: CONTINUE]
    Judge -->|Stagnation| End1[DECISION: END / Consensus]
    
    Continue1 --> Escalator
    Continue2 --> Escalator
    
    Escalator{Escalation Checker}
    Escalator -->|Iterations < 5| LoopBack((Next Round))
    Escalator -->|Iterations >= 5| End2[Hard Limit Escalate]
    
    End1 --> LoopEnd((Loop Terminates))
    End2 --> LoopEnd
    
    LoopBack -.-> Start
```

## 3. Tri-Model Strategy

The backend allocates specific reasoning models based on the cognitive complexity of the task, optimizing for both speed and depth.

```mermaid
pie title "Agent Model Allocation (Vertex AI: Global)"
    "gemini-3.1-flash-lite (Checkers, Triage)" : 3
    "gemini-3.5-flash (Judge)" : 1
    "gemini-3.1-pro-preview (Orchestrator, Debaters, Synthesizer)" : 4
```
