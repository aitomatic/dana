# Dana’s Out-of-the-Box Agentic Behavior Highlights

__Concurrency by default__ *(Concurrent pillar)*  
Function calls are executed concurrently without requiring `async` or thread management. Slow operations do not block others.  
[Example → `concurrency_by_default.na`](concurrency_by_default.na)

__Deterministic outputs via type casting__ *(Deterministic pillar)*  
`reason(...)` outputs can be cast into annotated types such as `int`, `float`, `dict`, or `struct`. This ensures predictable and verifiable results.  
[Example → `reason_type_casting.na`](reason_type_casting.na)

__Workflows as composition__ *(Composed pillar)*  
Functions can be composed in sequential, parallel, and conditional forms to build reusable workflows.  
[Example → `workflow_composition.na`](workflow_composition.na)