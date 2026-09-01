# Runbook: Pipeline Operations

## Ingesting & Refining Documentation

1. **Add URLs to Queue**:
   ```bash
   uv run --directory hub python scripts/pipeline_manager.py add https://docs.example.com/
   ```

2. **Run Pipeline Ingestion**:
   ```bash
   uv run --directory hub python scripts/pipeline_manager.py run
   ```

3. **Refine Docset**:
   ```bash
   PYTHONPATH=hub/scripts uv run --directory hub python -m docset_refine all ~/.global-ai-hub/text-mirror/docs.example.com.md
   ```

4. **Check Index Status**:
   ```bash
   uv run --directory hub python scripts/docset_indexer.py list
   ```
