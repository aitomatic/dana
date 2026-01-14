"""Demo: integrating Reflection with a learner-style workflow."""

from dana.core.memory import LTMemory, STMemory
from dana.core.reflection import Reflection


def main() -> None:
    # This shows the data flow a Learner would trigger at session end.
    stmem = STMemory()
    stmem.append("user", "Sync job failed overnight")
    stmem.append("agent", "Investigating logs and retry settings")
    stmem.append("observation", "Retries disabled for the job")
    stmem.append("agent", "Enabled retries; job completed")

    ltmem = LTMemory(path="./memories/")
    reflection = Reflection()
    result = reflection.run(stmemory=stmem, ltmemory=ltmem)

    print(result.summary)


if __name__ == "__main__":
    main()
