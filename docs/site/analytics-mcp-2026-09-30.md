# Google Analytics MCP setup and continuation

Version: 1.0.4
Date: 2026-09-30
Task: TASK-48, blocks website refocus TASK-43
Delta: the new stream tag is published at 9f420a3 on both domains. Clean checks, live browser collection and official MCP realtime ingestion passed. The installation and property-access requirements are complete; genuine audience measurement starts with this new property.

## Installed and authenticated state

The official `analytics-mcp` package, version 0.7.0, is installed in uv's isolated Python 3.13 tool environment. The launcher is `/Users/mitch/.local/bin/analytics-mcp`. `/Users/mitch/.codex/config.toml` enables the stdio server named `analytics-mcp`. The 28 previous server entries were preserved. The private configuration backup is `/Users/mitch/.codex/backups/config-before-analytics-mcp-20260930-033648.toml`.

Protocol initialization and discovery passed. The server exposes nine tools: `get_account_summaries`, `list_google_ads_links`, `get_property_details`, `list_property_annotations`, `get_custom_dimensions_and_metrics`, `run_report`, `run_realtime_report`, `run_funnel_report`, and `run_conversions_report`. These tools are now callable in this Codex session. Codex's `auth_status: unsupported` describes ADC authentication rather than Codex-managed OAuth; it does not mean authentication failed.

The dedicated Google Cloud project `llmsx-analytics-mcp` has the Analytics Admin and Data APIs enabled. The Desktop OAuth client and local ADC sign-in are complete. The granted scope is only `https://www.googleapis.com/auth/analytics.readonly`. Client JSON and ADC files have mode 0600 and remain outside this repository. No billing, trial or Gemini activation occurred.

The user created a Google Analytics account and website property on 2026-09-30. The official `get_account_summaries` call now exposes one account and one property. The official Admin SDK, using the same read-only ADC, verifies the sole web stream uses the supplied measurement ID `G-0E31PW5CE9`. Recent host/event reports and realtime stream/event reports execute successfully. Initial reports had zero rows before tag publication. After the deployment and browser verification, official MCP realtime reports show the verification page views, session starts and first visits on that stream. These are setup test visits, not evidence of genuine reader interest. The selected email is not proven by ADC; access to the property is verified by successful API calls.

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

## Publication and verification

Site version 0.0.6 replaces both prior ID occurrences in the shared Base.astro. The Google tag is immediately after head on public content documents, and private routes keep their existing exclusions. The clean release build validated one loader/config on 1,275 public documents, none on 11 strict documents, early charset declarations, matching static/edge CSP rules and the updated inline hash. Astro check has no errors or warnings; the full site suite passed all 254 tests. No generated tracked source drift occurred.

The isolated production commit is `9f420a348ba0f7644e21ee0839174b0ead65b0d0`. Site CI, full CI and Cloudflare deployment passed. The deployment is [bb63f7b4.llms-explorer.pages.dev](https://bb63f7b4.llms-explorer.pages.dev). Both domains passed 28 HTTP route checks each. Browser checks on each domain loaded gtag.js with HTTP 200 and sent a collection POST for G-0E31PW5CE9 that Google accepted with HTTP 204. Official MCP realtime reports then confirmed ingestion into the verified stream.

[Public verification](../verification/google-tag-2026-09-30.json) and [clean-build checks](../verification/google-tag-artifacts-2026-09-30.json) exclude private account identifiers, client identifiers, raw request parameters and audience reports. Raw API evidence remains private at `/tmp/llmsx-ga-mcp/new-property/postdeploy-realtime-9f420a3.json`.

The browser also observed a blocked Cloudflare runtime challenge script using `/cdn-cgi/challenge-platform/scripts/precursor/main.js`. Its dynamic inline hash is absent from the build-time CSP. It does not reference Google Analytics. Collection requests and realtime ingestion succeeded. The hash policy was preserved; no unsafe-inline permission was added. Review Cloudflare runtime injection separately if it affects visitor challenges.

## Ongoing measurement

The installation, tag publication and official MCP report access requirements are complete. Close TASK-51, TASK-48 and parent TASK-43 with this evidence. The new property has no earlier audience history, and the recorded setup visits do not measure reader value.

Continue the substantive curation plan. Once comparable real traffic exists, use engaged visits, public guide paths, acquisition and tool/library actions to prioritize improvements. Do not treat the installation checks as audience demand or claim a measured redesign effect. Renew the External Testing OAuth sign-in when needed as documented above. Search Console inspection and any later AdSense review remain separate follow-up work. No AdSense review request has been sent.
