# SKaaS public research and skill hosts

Both names use the existing Cloudflare-managed `skill-registry-mongo` tunnel.
Each DNS record is a proxied CNAME pointing to that tunnel’s UUID at
`cfargotunnel.com`. Each route forwards directly to its loopback service.

| Public host | Paths | Origin |
| --- | --- | --- |
| `skills-mcp.skaas.io` | `/mcp` | `http://127.0.0.1:8766` |
| `research-mcp.skaas.io` | `/mcp`, `/v1/writers`, `/v1/writers/{64 lowercase hex digits}` | `http://127.0.0.1:8767` |

[The rules](skaas-ingress.json) set each origin's HTTP Host header to the
loopback authority already accepted by its application. Both applications
continue to enforce request authorization. Writer enrollment and revocation
require an operator credential. Each legacy public host retains its own
MCP-only rule and existing DNS record.

## Check or apply the mapping

Run the script from a machine with `cf` signed in to the account managing both
zones and the tunnel. It checks that both legacy names resolve in the account
to that exact tunnel, the old routes target the expected services, the destination
names are free or already correct, and the final ingress fallback returns 404.

```sh
python3 hub/research-library/scripts/publish_skaas_domains.py
python3 hub/research-library/scripts/publish_skaas_domains.py --apply
```

The first command reads the configuration. The second preserves the current
tunnel settings, adds missing ingress rules, creates missing DNS records and
reads back both resources. Rerun it after a partial failure. Review any data
reported as conflicting before making changes.

## Verify the endpoints

Use normal network resolution and certificate verification for the following checks.

```sh
curl --silent --show-error --output /dev/null --write-out '%{http_code}\n' https://research-mcp.skaas.io/mcp
curl --silent --show-error --output /dev/null --write-out '%{http_code}\n' https://skills-mcp.skaas.io/mcp
```

Both return HTTP 401 for unauthenticated requests. An unregistered path returns
404. With the appropriate credentials supplied to the [standalone client](../client/library_client.py),
run `tools --service research` and `tools --service skills` to verify MCP
initialization and the tool inventories. Negative DNS answers from a resolver
can persist until their TTL expires. If organization policy blocks a newly seen
hostname, continue using that organization's approved endpoint during review.
