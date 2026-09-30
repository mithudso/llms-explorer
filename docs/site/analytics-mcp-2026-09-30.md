# Google Analytics MCP setup and continuation

Version: 1.0.1
Date: 2026-09-30
Task: TASK-48, blocks website refocus TASK-43
Delta: installs the official Analytics server and validates its tools; authenticated live reports remain pending. Revision 1.0.1 records the user login and dedicated project creation.

## Installed state

The official `analytics-mcp` package, version 0.7.0, is installed in uv's isolated Python 3.13 tool environment. The launcher is `/Users/mitch/.local/bin/analytics-mcp`. `/Users/mitch/.codex/config.toml` enables it as a stdio server named `analytics-mcp`. The 28 previous server entries were preserved. The private configuration backup is `/Users/mitch/.codex/backups/config-before-analytics-mcp-20260930-033648.toml`.

Protocol initialization succeeds with the server name Google Analytics MCP Server. Tool discovery returns nine tools: `get_account_summaries`, `list_google_ads_links`, `get_property_details`, `list_property_annotations`, `get_custom_dimensions_and_metrics`, `run_report`, `run_realtime_report`, `run_funnel_report`, and `run_conversions_report`. `codex mcp list --json` confirms the server is enabled. Its `auth_status: unsupported` indicates Google ADC authentication rather than Codex-managed OAuth.

The first `get_account_summaries` request returns `Your default credentials were not found.` No cached gcloud account, ADC, project environment or Desktop OAuth client JSON was found in the inspected standard locations. This failure is an authentication gap, not evidence about website traffic. No live report has been retrieved.

Private local validation artifacts are under `/tmp/llmsx-ga-mcp/`: `initialize.json`, `tools.json`, `account-summaries.json`, `server-stderr.log`, and `probe.py`. They may be removed by a reboot. They contain no retrieved audience reports. Credentials and raw account information must remain outside this repository.

## Connect an authorized account

Google's [official setup](https://github.com/googleanalytics/google-analytics-mcp#configure-credentials-) requires a Google Cloud project with the Analytics Admin and Data APIs enabled, and credentials authorized to read the relevant Analytics property. Desktop OAuth needs a local OAuth client JSON. A service account needs property access. The user signed into the opened Google Cloud Console. A dedicated project, `llmsx-analytics-mcp`, has now been created there. No billing, trial or Gemini activation occurred. The remaining OAuth client, read-only ADC and API setup is underway in that account.

A private helper is ready at `/Users/mitch/.local/share/analytics-mcp-setup/configure.py`. It validates the JSON type, project match and Google endpoints, requests Analytics read-only scope, backs up existing local ADC/configuration, and preserves unrelated MCP entries. It does not enable APIs. It has been checked with `--help`; interactive ADC OAuth has not yet completed.

```sh
# Validate the supplied Desktop client without changing configuration.
/Users/mitch/.local/share/analytics-mcp-setup/configure.py --project PROJECT_ID --client-json /absolute/path/desktop-client.json --check-only

# Run the local sign-in flow after validation.
/Users/mitch/.local/share/analytics-mcp-setup/configure.py --project PROJECT_ID --client-json /absolute/path/desktop-client.json

# Or configure a service account already granted property access.
/Users/mitch/.local/share/analytics-mcp-setup/configure.py --project PROJECT_ID --service-account-json /absolute/path/service-account.json
```

Replace placeholders with the actual supplied values. Do not commit the JSON or paste its secrets into chat. After authentication, re-run the official MCP probe and account/property lookup. A new Codex session may be needed for its tool list to include a newly installed server; the direct stdio probe already validates the configured launcher.

## Reports to collect and interpret

Verify that the chosen property represents llms-explorer.com or llmsx.org, then filter reports by those hostnames. Collect the last 28 completed days and a comparable prior period when tracking exists. Start with users, sessions, engaged sessions, engagement rate and page views; add top public page paths, acquisition channels and event names. Keep query strings, user-level information and private account identifiers out of committed reports.

The site measurement ID is `G-0KWFPMH6WX`. Tracking was added recently, so absent earlier tracking must not be interpreted as no visitors. Distinguish page views from genuine engagement. Check sample size, report thresholding and the dates covered before interpreting differences.

Use the findings to choose homepage features and follow-up guides, diagnose failed journeys, and establish a baseline for the concept tree, tool downloads and reusable skills. The implemented refocus is an editorial choice grounded in existing content; it has not yet been validated by live reader behavior.

## Remaining work

1. Complete the dedicated project OAuth client and private local credential setup.
2. Confirm the two Analytics APIs are enabled in that project; enable them if needed within the authorized setup.
3. Complete ADC sign-in with Analytics read-only scope.
4. Run account/property lookup and scoped reports through the official server.
5. Save privacy-conscious aggregate evidence and revise the site plan where warranted.

The user has authorized website publication. Deployment and AdSense review have not yet occurred. TASK-48 and TASK-43 remain open until this added live-data requirement is resolved.
