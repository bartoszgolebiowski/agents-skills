# AI Tutor System - GitHub Copilot Instructions

This repository contains a production-grade AI language tutoring system with a memory-augmented, skill-based agent architecture.

## Quick Reference

**What is this system?**

- Conversational AI for language learning
- Memory-augmented agents (multi-layer memory)
- Skill-based architecture (procedural memory pattern)
- State machine-driven conversation flow
- Context engineering with prompt templates

**Key Technologies:**

- Python 3.11+
- An LLM API with structured output capabilities
- A data validation library (like Pydantic) for schemas
- A templating engine (like Jinja2) for prompts
- A web framework (like Gradio) for UI

## Architectural Layers

This project is built on a clean, layered architecture. Understanding these layers is key to generating compliant code.

- **Execution Layer (`engine/`)**: Responsible for orchestration and execution. Contains agents that manage the conversation flow and are the single point of interaction with the LLM.
- **State Management Layer (`memory/`)**: The "brain" of the system. Defines all data structures (schemas) for the different layers of memory and contains the logic for all state modifications.
- **Capabilities Layer (`skills/`)**: Holds the declarative definitions for the AI's different conversational modes. Each skill defines a prompt template and an output structure, but contains no execution logic.
- **Persistence Layer (`persistence/`)**: Provides a pluggable backend for saving and loading user state.
- **Application Layer (`app.py`)**: The user-facing entry point, providing a UI for interaction.

## Architecture Principles

1.  **Agents vs. Skills**: Agents execute, Skills declare. Never mix these concerns.
2.  **Single LLM Call Point**: All interactions with the LLM must go through a single, designated Executor Agent.
3.  **Deterministic Routing**: Conversation flow is controlled by an explicit state machine that reads flags from memory, not by the LLM.
4.  **Immutable State**: State must never be mutated directly. Always create a deep copy before making modifications.
5.  **Memory-Driven**: The entire system is driven by the state. Routing, prompts, and outputs all depend on and modify the memory.

## Code Style

**Follow these patterns:**

✅ Skills are stateless and declarative
✅ Deep copy state before modifications
✅ Use type hints everywhere
✅ Use data models for all schemas
✅ Use a templating engine for all prompts
✅ Use `Optional[]` for nullable fields
✅ Docstrings with Args/Returns/Raises

**Avoid these anti-patterns:**

❌ LLM calls outside the designated Executor Agent
❌ State mutations without a deep copy
❌ Execution logic in skills
❌ Hardcoded values in prompt templates
❌ Multiple skills triggered by a single state
❌ Mixing data between memory layers

## When Generating New Code

**Guidance for Adding a Skill:**

1.  Define a structured data model for the skill's output.
2.  Create a `Skill` class that defines its prompt template and output model.
3.  Write a prompt template that injects context from memory.
4.  Register the new skill in a central registry.
5.  Implement the state update logic within the State Manager.
6.  Add the routing logic to the Coordinator's state machine.

**Guidance for Adding to Memory:**

1.  Define a new data schema for the data.
2.  Initialize the new schema within the initial state creation logic.
3.  Create a template to expose this memory to prompts.
4.  Include the new template in relevant skill prompts.

**Guidance for Routing Logic:**
Routing logic must be a pure function that reads flags from the `workflow` memory layer to determine the next step. It should not have side effects.

**Guidance for State Updates:**
State updates must be handled within the State Manager. Create a dedicated method to map the fields from a skill's structured output to the corresponding fields in the state. Always operate on a deep copy of the state.

## Path-Scoped Instructions

For component-specific guidance, see:

- `.github/instructions/architecture.instructions.md` - Overall system
- `.github/instructions/engine.instructions.md` - Agent layer
- `.github/instructions/memory.instructions.md` - Memory system
- `.github/instructions/skills.instructions.md` - Skills layer
- `.github/instructions/templates.instructions.md` - Prompt templates

```

```
