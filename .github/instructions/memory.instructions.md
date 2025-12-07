# Memory Component Instructions

## Guiding Principles

The Memory layer is the stateful core of the system. It defines the structure of all data and provides the logic for how that data is modified. It is designed to be a centralized, predictable, and robust state management system.

### Layer-Based Architecture

The memory is organized into a multi-layer system, inspired by cognitive psychology, to separate different types of information.

| Layer        | Purpose                                              | Lifespan   |
| :----------- | :--------------------------------------------------- | :--------- |
| **Core**     | The AI's fixed identity and persona (read-only).     | Permanent  |
| **Semantic** | Long-term, structured knowledge about the user.      | Long-term  |
| **Episodic** | A log of significant learning events and milestones. | Long-term  |
| **Workflow** | Flags and counters that drive the state machine.     | Session    |
| **Working**  | Short-term data, like the current conversation.      | Short-term |

### Immutability

State must be treated as immutable. Any function that modifies the state must:

1.  Create a **deep copy** of the incoming state object.
2.  Perform all modifications on the **copy**.
3.  Return the **new, modified state object**.
    This principle is critical for preventing side effects, ensuring predictable state transitions, and simplifying debugging.

### Structured Data Models

All data structures within the memory layers must be defined using a formal schema system (e.g., Pydantic). This provides:

- **Type Safety**: Prevents data corruption and runtime errors.
- **Validation**: Enforces rules and constraints on data.
- **Clarity**: Serves as self-documenting code for what the state looks like.

## State Management Logic

### State Initialization

- A dedicated function must be responsible for creating a complete, well-structured initial state for a new user.
- This function defines the "shape" of the entire state object. Every expected key for every layer must be present, even if its value is `None` or an empty collection (`[]`, `{}`). This prevents runtime errors from accessing non-existent keys.

### State Update Logic

- **Centralized Dispatch**: A single, top-level function should act as a dispatcher for all state updates. It receives the structured output from an executed skill.
- **Skill-Specific Handlers**: The dispatcher's role is to route the output to a dedicated update handler based on the skill that produced it. It should not contain any update logic itself.
- **Modular Updates**: Each skill must have its own corresponding update function. This function is responsible for mapping the fields from the skill's output object to the appropriate fields in the (copied) state. This ensures that state update logic is modular and easy to maintain.
- **Incremental Updates**: For multi-turn data collection, update handlers should check if a field in the skill's output is populated before overwriting existing state. This allows for gradual enrichment of the user's profile.

## Context Exposure via Templates

- **Declarative Templates**: The memory system should use a templating engine (e.g., Jinja2) to define how state information is exposed to the LLM.
- **Layered Includes**: Each memory layer should have its own template file. Skills can then include the templates for the memory layers they need, ensuring they only get the context relevant to their task.
- **No Hardcoded Strings**: Prompts should never be constructed with f-strings. Always use templates to inject context into prompts.

## Common Mistakes to Avoid

- **Don't mutate the original state object.** Always make a deep copy first.
- **Don't use unstructured dictionaries for complex data.** Define a schema model.
- **Don't mix data between memory layers.** Workflow flags belong in the `workflow` layer, not the `semantic` layer.
- **Don't write monolithic update functions.** Create a separate, dedicated update handler for each skill.
- **Don't access state keys that might not exist.** Ensure the initial state object is fully populated with default values.
