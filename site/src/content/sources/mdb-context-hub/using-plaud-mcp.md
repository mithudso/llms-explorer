---
title: "Plaud MCP Integration"
description: "You have access to 11 MCP tools, 4 prompts, and 12 skill resources for managing Plaud AI recordings, transcripts, and memory. Each tool returns structured JSON with next_steps guidance."
---

# Plaud MCP Tools — Quick Start

You have access to 11 MCP tools, 4 prompts, and 12 skill resources for managing Plaud AI recordings, transcripts, and memory. Each tool returns structured JSON with `next_steps` guidance.

## Prerequisites

- MCP server configured in `.mcp.json` — authenticated via GitHub OAuth (automatic)
- `ELEVENLABS_API_KEY` env var — only needed for ElevenLabs transcription

## Tool Quick Reference

| Tool | Purpose | Skill |
|------|---------|-------|
| `find_recordings` | Browse and filter recordings | recording-search |
| `get_recording` | Full recording metadata | recording-search |
| `get_audio_url` | Presigned download URL (5min expiry) | recording-search |
| `transcribe` | ElevenLabs transcript (cached or live) | transcription |
| `get_content` | AI summary or meeting notes | transcription |
| `trigger_processing` | Plaud server-side AI processing | transcription |
| `get_account_info` | Account profile and membership | -- |
| `get_processing_status` | AI processing queue status | -- |
| `list_languages` | Supported language codes | transcription |
| `memory_search` | Semantic search across transcripts | memory-search |
| `memory_ingest` | Bulk index recordings into memory | bulk-operations |

## Prompts

MCP clients can discover and invoke these workflow templates:

| Prompt | Purpose | Parameters |
|--------|---------|------------|
| `daily_briefing` | Status overview — recent recordings, queue, memory | None |
| `analyze_transcript` | Deep analysis of a recording | `file_ref` |
| `search_memory` | Guided dual-path search | `query`, `time_range` (default "7d") |
| `bulk_summary` | Summarize multiple recordings | `count` (default 5) |

## File ID Resolution

All tools accepting `file_ref` support three formats:

| Format | Example |
|--------|---------|
| Full ID | `4f757af256ecba4fab502739c122dc78` |
| Short prefix | `4f75` |
| Row number | `3` (from last `find_recordings`) |

Row numbers persist across tool calls within a session — call `find_recordings` once, then use row numbers in subsequent `transcribe`, `get_content`, etc. calls.

## Cost Safety

Tools that consume external credits prompt for confirmation via MCP elicitation:

- `transcribe` — asks before calling ElevenLabs API (cached transcripts are free)
- `memory_ingest(source="all")` — asks before bulk operations that may trigger transcriptions

Older MCP clients that don't support elicitation skip the prompt and proceed directly.

## Skills as Resources

The MCP server exposes plugin skills as MCP resources — any client can discover and read them without installing the plugin:

```
skill://recording-search/SKILL.md
skill://memory-search/SKILL.md
skill://transcription/SKILL.md
skill://bulk-operations/SKILL.md
skill://using-plaud-mcp/SKILL.md
skill://using-plaud-cli/SKILL.md
```

## Setup

The MCP server is configured in the plugin's `.mcp.json`. Authentication uses GitHub OAuth — Claude handles the flow automatically on first connect. See the plugin README for details.

## See Also

- **recording-search** — Browsing, filtering, and metadata retrieval
- **memory-search** — Semantic search across indexed transcripts
- **transcription** — ElevenLabs transcription with cost awareness
- **bulk-operations** — Batch ingestion, auto-polling, and export
- **using-plaud-cli** — CLI usage guide (`plaud` command)
