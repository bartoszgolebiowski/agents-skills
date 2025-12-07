"""Command-line entrypoint for the restaurant reservation agent."""

from __future__ import annotations

import sys

from engine.conversation import ReservationAgent

## omimport env

from dotenv import load_dotenv

load_dotenv()


def run_cli() -> None:
    """Start a simple CLI loop to interact with the agent."""

    agent = ReservationAgent()
    print("=== Symulacja gościa rezerwującego stolik w Atut Bistro ===")
    print(
        "Odpowiadaj jako obsługa restauracji. Wpisz wiadomość i naciśnij Enter (quit, aby zakończyć).\n"
    )

    try:
        reply = agent.step()
        print(f"Aura: {reply}")
        while True:
            if agent.is_complete():
                print("\nProces zakończony.")
                break
            user_message = input("Ty: ").strip()
            if user_message.lower() in {"quit", "exit"}:
                print("Kończę rozmowę. Do zobaczenia!")
                break
            if not user_message:
                continue
            reply = agent.step(user_message)
            print(f"Aura: {reply}")
    except KeyboardInterrupt:
        print("\nPrzerwano rozmowę. Do zobaczenia!")
    except Exception as exc:  # pragma: no cover
        print(f"Wystąpił nieoczekiwany błąd: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    run_cli()
