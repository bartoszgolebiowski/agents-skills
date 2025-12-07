# Restaurant Reservation Agent

This project implements a state-driven conversational agent that role-plays a diner trying to reserve a table at a restaurant. The architecture follows the layered pattern described in the repository instructions:

- **engine/** – coordinator and executor agents.
- **memory/** – immutable state schemas plus the state manager.
- **skills/** – declarative skill definitions with structured outputs.
- **templates/** – Jinja templates for prompts and memory exposure.
- **persistence/** – persistence adapters (placeholder for now).

## Running with OpenRouter

1. Install dependencies: `pip install -e .`
2. Copy `.env.example` to `.env` and set `OPENROUTER_API_KEY` (plus optional overrides below). The app automatically loads the `.env` file on startup.
3. (Optional) override defaults:
   - `OPENROUTER_MODEL` – e.g. `anthropic/claude-3.5-sonnet`
   - `OPENROUTER_TEMPERATURE` – float, default `0.2`
   - `OPENROUTER_MAX_OUTPUT_TOKENS` – int, default `1200`
4. Run `python app.py` to start the conversation loop (the agent will speak as the guest, you can respond as the restaurant staff).

The OpenRouter client is wrapped with [Instructor](https://github.com/jxnl/instructor) so every skill automatically receives structured, Pydantic-validated outputs.

For offline tests you can still pass the deterministic stub through `ReservationAgent(llm_client=StubLLMClient())`.
