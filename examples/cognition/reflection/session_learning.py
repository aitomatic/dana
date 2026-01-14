"""Demo: run four-phase reflection to distill STMemory into LTMemory."""

from dana.core.memory import LTMemory, STMemory
from dana.core.reflection import Reflection


def main() -> None:
    stmem = STMemory()
    stmem.append("user", "The deploy is failing")
    stmem.append("agent", "Checking CI logs...")
    stmem.append("observation", "Missing env var: DATABASE_URL")
    stmem.append("agent", "Added to .env.example, deploy succeeded")
    stmem.append("user", "Thanks! Always forget that one")

    ltmem = LTMemory(path="./memories/")
    reflection = Reflection()
    result = reflection.run(stmemory=stmem, ltmemory=ltmem)

    print("=== Reflection Phases ===")
    for phase, output in result.phases.items():
        print(f"\nPhase - {phase.title()}:\n{output}")

    print("\n=== Result ===")
    print(f"Summary: {result.summary}")
    print(f"Memories created: {len(result.memories_created)}")


if __name__ == "__main__":
    main()
