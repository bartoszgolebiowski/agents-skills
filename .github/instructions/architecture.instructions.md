# Architecture Instructions

This document outlines the high-level architectural principles for the AI Tutor system. The architecture is designed to be modular, state-driven, and easily extensible. It enforces a strict separation of concerns between conversation logic, state management, and execution.

## Core Principles

1.  **Separation of Concerns**: The system is divided into distinct layers, each with a single responsibility.

    - **Application Layer**: Handles user interaction and presentation.
    - **Execution Layer**: Orchestrates the conversation and interacts with the LLM.
    - **State Management Layer**: Manages all data and state changes.
    - **Capabilities Layer**: Defines the AI's conversational skills.
    - **Persistence Layer**: Handles saving and loading state.

2.  **State-Driven Flow**: The conversation is not controlled by the LLM. Instead, a deterministic state machine reads flags from memory to decide the next action. The LLM's role is to provide structured data, not to drive the flow.

3.  **Immutable State**: State should be treated as immutable. Any modification must be done on a deep copy of the state object to ensure predictability and prevent side effects.

4.  **Declarative Capabilities**: AI skills are defined declaratively. They specify _what_ the AI can do (prompt and output structure) but not _how_ to do it (execution logic).

## Request Processing Flow

The system processes user requests through a well-defined, deterministic flow that relies on state, not on LLM improvisation.

1.  **Input Reception**: The application layer receives the user's message.
2.  **State-Based Routing**: A central coordinator agent examines the current `workflow` state from memory. Based on predefined flags and conditions, it determines which skill should be executed next. This is a deterministic decision, not a probabilistic one.
3.  **Skill Execution**: The coordinator passes control to an executor agent.
4.  **LLM Interaction**: The executor agent is the _only_ component that interacts with the LLM. It:
    a. Loads the selected skill definition (prompt template and output schema).
    b. Gathers the necessary context from various memory layers.
    c. Renders the prompt template with the context.
    d. Sends the request to the LLM and receives a structured data response.
5.  **Structured Output**: The executor agent returns the structured data received from the LLM. It does not modify the state.

## Memory Update Flow

State modifications are handled centrally and explicitly after a skill has been executed.

1.  **Output Reception**: The state manager receives the structured output from the executed skill.
2.  **Dedicated Update Logic**: The state manager dispatches the output to a specific function responsible for updating the state based on that skill's output. Each skill should have a corresponding, dedicated update handler.
3.  **State Modification**: The handler creates a deep copy of the current state.
4.  **Targeted Updates**: The handler maps the fields from the skill's output to the appropriate schemas within the new state object.
5.  **State Replacement**: The newly modified state object replaces the old one.

This ensures that all state changes are predictable, traceable, and decoupled from the execution logic.
