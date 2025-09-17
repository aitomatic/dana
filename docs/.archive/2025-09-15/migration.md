## Migration for docs/examples/

Use these top-level `examples/` replacements:

- docs/examples/first-agent.na → examples/first_agent.na
- docs/examples/local_agent.na → examples/resources_file_io.na
- docs/examples/production.na → examples/workflows_data_pipeline.na (or workflows_sequential.na)
- docs/examples/multi_agent.na → examples/workflows_multi_agent_chat.na
- docs/examples/chatbot.na → covered by workflows_multi_agent_chat.na
- docs/examples/data-processor.na → examples/workflows_data_pipeline.na
- docs/examples/data_processor.na → examples/workflows_data_pipeline.na

Run with:

```bash
dana run examples/first_agent.na
```


