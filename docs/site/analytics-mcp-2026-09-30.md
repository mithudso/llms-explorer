# Google Analytics MCP setup and continuation

Version: 1.0.3
Date: 2026-09-30
Task: TASK-48, blocks website refocus TASK-43
Delta: the user created a new GA4 account/property and supplied G-0E31PW5CE9. Property access, stream mapping and read-only MCP reports now work. The tag update is awaiting validation and production publication.

## Installed and authenticated state

The official `analytics-mcp` package, version 0.7.0, is installed in uv's isolated Python 3.13 tool environment. The launcher is `/Users/mitch/.local/bin/analytics-mcp`. `/Users/mitch/.codex/config.toml` enables the stdio server named `analytics-mcp`. The 28 previous server entries were preserved. The private configuration backup is `/Users/mitch/.codex/backups/config-before-analytics-mcp-20260930-033648.toml`.

Protocol initialization and discovery passed. The server exposes nine tools: `get_account_summaries`, `list_google_ads_links`, `get_property_details`, `list_property_annotations`, `get_custom_dimensions_and_metrics`, `run_report`, `run_realtime_report`, `run_funnel_report`, and `run_conversions_report`. These tools are now callable in this Codex session. Codex's `auth_status: unsupported` describes ADC authentication rather than Codex-managed OAuth; it does not mean authentication failed.

The dedicated Google Cloud project `llmsx-analytics-mcp` has the Analytics Admin and Data APIs enabled. The Desktop OAuth client and local ADC sign-in are complete. The granted scope is only `https://www.googleapis.com/auth/analytics.readonly`. Client JSON and ADC files have mode 0600 and remain outside this repository. No billing, trial or Gemini activation occurred.

The user created a Google Analytics account and website property on 2026-09-30. The official `get_account_summaries` call now exposes one account and one property. The official Admin SDK, using the same read-only ADC, verifies the sole web stream uses the supplied measurement ID `G-0E31PW5CE9`. Recent host/event reports and realtime stream/event reports execute successfully. Initial reports have zero rows before tag publication. The selected email is not proven by ADC; access to the property is verified by successful API calls.

Earlier failures were `Your default credentials were not found.` and an Analytics Admin API `SERVICE_DISABLED` response. Credentials and API enablement resolved those failures. The later empty account list was resolved when the user created the new property.

## Local connection and maintenance

Google's [official setup](https://github.com/googleanalytics/google-analytics-mcp#configure-credentials-) requires ADC and the two Analytics APIs. A private helper is at `/Users/mitch/.local/share/analytics-mcp-setup/configure.py`. It validates the supplied client, project and Google endpoints. It uses google-auth-oauthlib InstalledAppFlow with PKCE and a localhost callback. It backs up local ADC/configuration and preserves other MCP entries. This avoids gcloud's additional cloud-platform scope requirement.

```sh
# Validate the existing Desktop client without changing configuration.
/Users/mitch/.local/share/analytics-mcp-setup/configure.py --project llmsx-analytics-mcp --client-json /Users/mitch/.local/share/analytics-mcp-setup/desktop-client.json --check-only

# Authorize the account that can read the website's Analytics property.
/Users/mitch/.local/share/analytics-mcp-setup/configure.py --project llmsx-analytics-mcp --client-json /Users/mitch/.local/share/analytics-mcp-setup/desktop-client.json
```

The OAuth app remains External Testing. If a different account must authorize, add that account as a test user before sign-in. Google documents a [seven-day refresh-token expiry](https://developers.google.com/identity/protocols/oauth2#expiration) for External Testing apps with scopes such as Analytics. Renew local sign-in when needed. Publishing or verifying the OAuth app is a separate maintenance choice and has not occurred.

The completed OAuth URL and callback are no longer reusable. Generate a fresh flow when reauthorization is needed. Credentials, callback codes and tokens must not be pasted into chat or committed.

Private validation artifacts are under `/tmp/llmsx-ga-mcp/`; they may be removed by a reboot. Initial probe artifacts record the earlier authentication failure. `account-summaries-authenticated.json` records the earlier empty result. New property mapping and initial report evidence are under `/tmp/llmsx-ga-mcp/new-property/` with restricted permissions. A private collector is ready at `/Users/mitch/.local/share/analytics-mcp-setup/collect_reports.py`. It calls the official stdio server and stores account information and reports privately. No private audience evidence belongs in the public repository.

## Reports to collect and interpret

Property access and exact measurement-ID mapping are now verified. The recent report filters `hostName` to llms-explorer.com or llmsx.org, including their www hostnames. The realtime API does not support `hostName`; use its stream/event dimensions and keep this limitation explicit.

Collect the last 28 completed days and a comparable prior period when tracking exists. Start with users, sessions, engaged sessions, engagement rate and page views. Add top public page paths, landing pages, acquisition channels and event names. Exclude query strings, private account/key/playground routes, user-level information and private account identifiers from committed evidence.

The current measurement ID is `G-0E31PW5CE9`, replacing `G-0KWFPMH6WX`. This property was created on 2026-09-30 and starts a fresh collection history after the tag is published. Initial empty reports cannot describe earlier readership. Check sample size, report thresholding and date coverage before interpreting differences. The refocus has no measured post-launch effect yet. Installation checks generate test visits; do not present them as genuine reader interest.

Use actual findings to prioritize homepage features and follow-up guides, diagnose failed journeys, and establish a baseline for the concept tree, tool downloads and reusable skills. The implemented refocus remains an editorial choice grounded in existing content; live reader behavior has not yet validated it.

## Remaining work

1. Validate and publish the single shared tag update under the existing live-publication authorization.
2. Verify the new tag and actual collection requests on both production domains; private routes remain excluded.
3. Rerun official MCP reports after collection. Keep test hits distinct from genuine reader interest.
4. Record publication evidence and complete TASK-51, TASK-48 and parent TASK-43 when their required checks pass.

The website refocus is published and verified at `89ca431`; the new tag update is in progress. See [publication and verification](refocus-2026-09-30.md). No AdSense review request has been sent.
