# Pipeline Module (`opendxa.execution.pipeline`)

This module provides the core components for building and executing data processing pipelines within the OpenDXA framework.

## Overview

The Pipeline system allows you to define complex workflows as directed graphs, where nodes represent processing steps (like data sources, transformations, model inferences, and data sinks) and edges represent the flow of data between these steps. It builds upon the `ExecutionGraph` from the [Base Execution Framework](../../base/execution/README.md) and integrates seamlessly with the [Resource System](../../base/resource/README.md) by treating pipelines themselves as manageable resources.

Key features include:

*   Graph-based definition of data flows.
*   Asynchronous execution support.
*   Integration as discoverable `BaseResource` instances.

## Core Components

*   **`Pipeline`**: The main class, inheriting from `ExecutionGraph` and `BaseResource`, used to define and manage pipeline instances.
*   **`PipelineNode`**: Base class for nodes within a pipeline (though typically nodes inherit directly from `BaseNode`).
*   **`PipelineContext`**: Used to pass state and data through the pipeline execution.

## Further Reading

For detailed concepts, architecture, usage examples, and best practices, please refer to the main documentation:

*   **[Pipeline System Concepts](../../../docs/details/pipeline_system.md)**

---
<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the <a href="../../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
