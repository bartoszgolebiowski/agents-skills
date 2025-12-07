"""Command-line entrypoint for the restaurant reservation agent."""

from __future__ import annotations

import sys
from datetime import date, time

from engine.conversation import ReservationAgent
from memory.models import DesiredReservation, SemanticMemory
from dotenv import load_dotenv

load_dotenv()


def run_cli() -> None:
    """Start a simple CLI loop to interact with the agent."""

    # Create default Sarah Mitchell profile
    semantic_memory = SemanticMemory.create(
        guest_name="Sarah Mitchell",
        guest_phone="+1-555-123-4567",
    )

    desired_reservation = DesiredReservation(
        party_size=4,
        occasion="dinner",
        special_requests="table near the window with sunset view",
    )

    agent = ReservationAgent(
        semantic_memory=semantic_memory,
        desired_reservation=desired_reservation,
    )
    print("=== Restaurant Reservation Simulation ===")
    print(
        "Reply as the restaurant staff. Type your message and press Enter (quit to exit).\n"
    )

    try:
        reply = agent.step()
        print(f"Agent: {reply}")
        while True:
            if agent.is_complete():
                print("\nProcess completed.")
                break
            user_message = input("You: ").strip()
            if user_message.lower() in {"quit", "exit"}:
                print("Ending conversation. Goodbye!")
                break
            if not user_message:
                continue
            reply = agent.step(user_message)
            print(f"Agent: {reply}")
    except KeyboardInterrupt:
        print("\nConversation interrupted. Goodbye!")
    except Exception as exc:  # pragma: no cover
        print(f"An unexpected error occurred: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    run_cli()
