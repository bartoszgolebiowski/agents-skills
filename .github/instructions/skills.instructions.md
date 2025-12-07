# Skills Component Instructions

## Guiding Principles

The Skills layer contains the declarative definitions of the AI's capabilities. A skill defines _what_ the agent can do, but contains no logic for _how_ to do it. They are the "procedural memory" of the system, encoding the steps for different conversational tasks.

### The Definition of a Skill

A Skill is a stateless, declarative component with two primary parts:

1.  **A Prompt Template**: A template (e.g., using Jinja2) that defines the instructions and context to be sent to the LLM. It specifies the AI's persona, the task to be performed, and the required output format. It is responsible for dynamically injecting information from the system's memory into the prompt.
2.  **A Structured Output Model**: A data schema (e.g., a Pydantic model) that defines the exact structure, types, and constraints of the data that the LLM is expected to return.

### Core Rule: No Execution Logic

- Skills **must not** contain any imperative or operational logic.
- They **must not** make API calls, interact with external systems, or manage state.
- A skill's only "logic" is the rendering of its prompt template based on the context it receives.

## Skill Design and Structure

### The Output Model

- Every skill must be associated with a structured output model.
- This model serves as the contract between the skill and the execution engine.
- It must include a field for the conversational AI response (`ai_response`) and can include any number of other fields for structured data extraction, metadata, or state flags.
- For skills that involve a multi-step process (like data collection), the model should include a boolean flag (e.g., `is_complete`) to signal when the skill's objective has been met.

### The Prompt Template

- The template is the "brain" of the skill. It should be designed for clarity and consumption by an AI.
- **Structure**: Use clear sections, headers, and lists to organize the prompt.
- **Context Injection**: The template must be ableto access and render data from all layers of the system's memory.
- **Conditional Logic**: Use template logic (e.g., `{% if %}` blocks) to dynamically change the instructions based on the current state (e.g., providing different guidance for a beginner vs. an advanced user).
- **Output Instructions**: The template must explicitly instruct the LLM to provide its response in a format that matches the skill's output model.

## Creating New Skills

Adding a new capability to the system means creating a new skill and integrating it into the architecture.

1.  **Define the Output Schema**: Create a structured data model that defines the information you expect the LLM to return for this skill.
2.  **Create the Skill Class**: Define a class that represents the skill. This class should provide access to its prompt template and its output model.
3.  **Write the Prompt Template**: Create the template file. Inject context from memory, provide clear instructions, and specify the required output format.
4.  **Register the Skill**: Make the new skill discoverable by adding it to a central registry that the execution engine can query.
5.  **Implement State Update Logic**: In the memory management layer, create a dedicated function to handle the state changes that should occur after this skill is successfully executed.
6.  **Add Routing Logic**: In the coordinator agent, add a condition to the state machine that determines when this new skill should be triggered.

## Common Mistakes to Avoid

- **Don't add execution logic in skills.** A skill should never contain a method that makes an API call or performs an action. Its role is to be a blueprint, not a worker.
- **Don't store state in skill instances.** Skills must be stateless singletons. All necessary information should be passed in as context during prompt rendering.
- **Don't hardcode values in templates.** Always inject dynamic values (like names, levels, or goals) from the memory context.
- **Don't create skills without a structured output model.** The entire system relies on the predictable, validated data structures that these models enforce.
