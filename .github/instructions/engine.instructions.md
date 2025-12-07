# Engine Component Instructions

## Guiding Principles

The Engine layer is responsible for orchestration and execution. It acts as the "CPU" of the system, driving the conversation forward based on the current state. It is composed of agents, which are active components that perform tasks.

### Agent vs. Skill Separation

- **Agents** are for **imperative execution**. They contain the logic for _how_ to do things, such as calling an LLM, routing decisions, or managing state transitions.
- **Skills** are for **declarative definition**. They define _what_ the AI can do, such as the content of a prompt and the structure of its output.
- **Rule**: Never mix execution logic in skills, and never embed prompt templates or output schemas within agents.

### Single Responsibility Principle

Each agent in the engine must have a single, clearly defined purpose.

- **Coordinator Agent**: Its sole responsibility is to act as a state machine. It reads the current state from memory and deterministically decides which skill to execute next. It orchestrates the overall flow but does not execute any skills itself.
- **Executor Agent**: Its sole responsibility is to interact with the LLM. It takes a skill, prepares the necessary context from memory, renders the prompt, executes the LLM call, and returns the resulting structured data.

### LLM Interaction Policy

- **Single Point of Contact**: All LLM calls **must** go through the Executor Agent. This is the only component in the entire system authorized to communicate with the LLM.
- **No Side Effects**: The Executor Agent's job is to get structured data from the LLM. It must not modify the application state.

## Core Agent Responsibilities

### The Coordinator Agent (State Machine)

The Coordinator Agent implements the system's core routing logic. It must be a pure function with no side effects.

- **Input**: It should only accept the current `state` as input.
- **Logic**: It must contain explicit, non-AI-driven conditional logic that reads flags from the `workflow` portion of the state.
- **Output**: It must return a unique identifier for the skill that should be executed next.
- **Principle**: The logic should follow a sequential "waterfall" model, checking for the first incomplete step in a process and returning the corresponding skill. If all steps are complete, it should return a default or general-purpose skill.

### The Executor Agent (LLM Interaction)

The Executor Agent is the heart of the execution engine. Its role is to manage the interaction with the LLM for a given skill.

1.  **Skill Loading**: Dynamically load the required skill definition.
2.  **Context Preparation**: Assemble a `context` object containing the full `state` and any other data required by the skill's prompt template.
3.  **Prompt Rendering**: Delegate the final prompt creation to the skill by calling a method on the skill object (e.g., `prepare_prompt(context)`). The agent itself should not build the prompt string.
4.  **LLM API Call**: Execute the call to the LLM, ensuring it requests a structured response that matches the skill's defined output model.
5.  **Return Value**: The method must return the structured data object received from the LLM. It should not handle memory updates or conversation history.

## Common Mistakes to Avoid

- **Don't add LLM calls outside the Executor Agent.** The system must have a single, controlled point of interaction with the LLM.
- **Don't let the LLM decide the next skill.** Routing must be deterministic and controlled by the Coordinator Agent's state machine logic.
- **Don't put routing logic in handlers or skills.** All routing decisions belong in the Coordinator Agent.
- **Don't have the Executor Agent modify state.** Its job is to fetch data from the LLM, not to manage the application's state.
