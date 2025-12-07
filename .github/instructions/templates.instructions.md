# Templates Component Instructions

## Guiding Principles

The template system is the mechanism for **context engineering**. It translates the application's state into a structured, instruction-rich prompt for the LLM. The templates are a critical part of the system's "procedural memory," defining how the AI should behave in any given situation.

### Core Concepts

1.  **Declarative Context**: Templates declare _what_ information the LLM needs, not how to get it. They are the bridge between the `memory` and `engine` layers.
2.  **Separation of Concerns**: Templates separate the prompt's content and structure from the execution logic. The agents know _when_ to use a template, but the template itself knows _what_ to say.
3.  **Designed for AI**: Prompts are not just natural language; they are structured documents designed to be easily parsed and understood by an LLM. Clarity, structure, and explicit instructions are paramount.

## Template Architecture

The system uses a two-level, composable template architecture.

1.  **Memory Layer Templates**:

    - Each major layer of memory (`core`, `semantic`, `episodic`, etc.) has its own dedicated template.
    - The responsibility of a memory template is to expose the data from its corresponding memory layer in a structured, readable format.
    - These are the reusable building blocks of the context.

2.  **Skill Layer Templates**:
    - Each skill has a corresponding template that defines the prompt for that specific task.
    - A skill template's primary job is to compose the necessary memory templates and add task-specific instructions, guidelines, and output formatting rules.
    - This is achieved by "including" the required memory templates. For example, a tutoring skill might include the `semantic` and `episodic` templates to get context about the student and their learning history.

## The Structure of a Skill Template

A well-designed skill template is a structured document that guides the LLM through its reasoning process. It should contain several key sections:

1.  **Identity and Task Definition**: The template must begin by establishing the AI's persona and clearly stating the primary goal of the skill.
2.  **Context Injection**: This section assembles the situational context by including the relevant memory templates. It provides the LLM with all the information it needs about the user, the conversation history, and the current workflow state.
3.  **Dynamic Strategy**: Using conditional logic, this section adapts the AI's instructions based on the current state. For example, it might instruct the AI to use simpler language for a beginner-level user or to focus on a specific recurring mistake detected in the episodic memory.
4.  **Conversation Guidelines**: Provides explicit, high-level rules for the AI's behavior, such as its tone, how it should handle corrections, or what topics to avoid.
5.  **Output Formatting**: This is one of the most critical sections. It must give the LLM precise instructions on the structure of its response, ensuring it conforms to the skill's output model. It should detail every field the LLM is expected to return.

## Template Design Best Practices

- **Be Explicit**: Never assume the LLM knows what to do. Provide clear, unambiguous instructions for every part of the task.
- **Use Structure**: Organize prompts with clear headers, sections, and lists. A scannable document is easier for an LLM to parse and follow.
- **Leverage Conditional Logic**: The power of the template system comes from its ability to dynamically adapt. Use conditional blocks to handle different states, edge cases (like the first message in a conversation), or user levels.
- **Keep It Focused**: Only include the memory and context that is directly relevant to the skill's task. Overloading the prompt with unnecessary information can confuse the LLM and degrade performance.
- **Provide Examples**: For complex output formats, providing a one-shot or few-shot example within the prompt can dramatically improve the reliability of the LLM's response.

## Common Mistakes to Avoid

- **Hardcoding Values**: Never hardcode information that exists in memory. Always use template variables to inject data like user names, levels, or goals.
- **Assuming Data Exists**: Always use conditional logic to check for the existence of optional data before trying to render it. This prevents errors and makes the system more robust.
- **Overly Complex Logic**: While conditional logic is powerful, overly nested or complex logic can make templates difficult to read and debug. Keep it as simple as possible.
- **Vague Output Instructions**: Do not just ask for a "JSON response." Specify the exact keys, types, and a description for each field you expect in the output model.
