---
title: "A2A Protocol Interoperability"
description: "Reference for the Agent-to-Agent protocol and cross-framework agent communication."
---

# A2A Protocol & Agent Interoperability

Reference for the Agent-to-Agent protocol and cross-framework agent communication.

## When to use this skill

Activate when the user:
- asks about the A2A protocol or agent-to-agent communication
- wants to publish an Agent Card at `.well-known/agent.json`
- needs to implement A2A task lifecycle handling
- asks how A2A and MCP work together
- wants cross-framework agent interop (LangGraph &lt;-> CrewAI &lt;-> ADK &lt;-> Claude SDK)
- asks about AAIF, ACP, ANP, or agent protocol governance
- needs to design a multi-vendor agent system

## Quick reference

### A2A vs MCP

| Aspect | MCP | A2A |
| --- | --- | --- |
| Direction | Vertical (agent -> tools) | Horizontal (agent -> agent) |
| Abstraction | Stateless function calls | Stateful multi-turn tasks |
| Discovery | Server capabilities | Agent Cards at `.well-known/agent.json` |
| Transport | stdio / Streamable HTTP | JSON-RPC 2.0 over HTTPS + SSE |
| State management | None | 8-state task lifecycle |

### Task lifecycle (8 states)

```
SUBMITTED -> WORKING ----+----> COMPLETED (terminal)
               |         |----> FAILED (terminal)
               |         +----> CANCELED (terminal)
               |
               +----> INPUT_REQUIRED (interrupted)
               +----> AUTH_REQUIRED (interrupted)
               +----> REJECTED (terminal)
```

### Core JSON-RPC operations

| Operation | Method | Purpose |
| --- | --- | --- |
| SendMessage | `tasks/send` | Initiate or continue a task |
| SendStreamingMessage | `tasks/sendSubscribe` | Real-time SSE updates |
| GetTask | `tasks/{id}` | Retrieve current task state |
| CancelTask | `tasks/{id}/cancel` | Request cancellation (idempotent) |

**Required header:** `A2A-Version: Major.Minor` in all requests.

## Governance (2026)

- **AAIF** (Agentic AI Foundation, Linux Foundation): neutral governance body for A2A and MCP.
- **ACP**: merged into A2A under AAIF.
- **ANP**: emerging decentralized peer-to-peer discovery layer above A2A.

## References

- [A2A Protocol Specification](https://a2a-protocol.org/latest/specification/)
- [A2A GitHub Repository](https://github.com/a2aproject/A2A)
