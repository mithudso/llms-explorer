# SK MongoDB Research Kit

Run focused research, concept-family exploration, recursive discovery, and the
full research suite against one versioned research library. Shared sources,
claims, queue entries, and resumable runs stay in MongoDB through its HTTPS MCP
service. A coworker needs this kit, a supported agent client, and a separately
issued service capability.

| Workflow | Claude Code | Codex portable router |
| --- | --- | --- |
| Focused research | `/sk:dr topic` | `$sk dr topic` |
| Concept families | `/sk:cfe topic` | `$sk cfe topic` |
| Recursive exploration | `/sk:rabbithole topic` | `$sk rabbithole topic` |
| Full suite | `/sk:full-suite topic` | `$sk full-suite topic` |

Codex's native plugin exposes qualified skills through `/skills` and `$`
completion. Select the names returned by your client. Claude's `/sk:...` syntax
is its native plugin namespace; this kit does not promise those slash commands
in Codex. Queue and frontier options are available through the workflows.

Start with [SETUP.md](SETUP.md). The kit includes a native plugin for both clients,
the `$sk` router, complete methodology references, a preview-first installer,
and a standalone read-only HTTPS client. It includes no credentials, database
URI, client configuration, source corpus, research bodies, or server runtime.
Installation starts no research and does not replace existing global workflows.

The manifest binds every file to its SHA-256 and the source repository revision.
Checks detect corruption and unexpected files; they do not authenticate who
supplied an archive. Obtain the archive and its published digest from a source
you trust. Keep issued credentials outside the extracted kit.
