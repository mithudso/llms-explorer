---
title: "Slack Developer Platform"
description: "Use when building Slack apps, calling Web API methods, building Block Kit UIs, handling Events, configuring OAuth, or using the Slack MCP server. For auditing slash command registrations, orphaned sub"
---

# Slack Platform — Developer

## When to use this skill

Use when building Slack apps, calling Web API methods, building Block Kit UIs, handling Events, configuring OAuth, or using the Slack MCP server. For auditing slash command registrations, orphaned subscriptions, or bot token scope creep, use `slack-subscription-auditor` instead.

---

## 1. Platform Architecture

### Two App Paradigms

| Paradigm | Runtime | SDK | Deploy |
|---|---|---|---|
| **Bolt apps** | Node.js / Python / Java | Bolt SDK + Web API | Self-hosted, any server |
| **Deno Slack SDK apps** | Deno (serverless) | Built-in functions/triggers/workflows | Slack-managed infrastructure |

### Core Concepts

- **Web API** — HTTP RPC at `https://slack.com/api/METHOD.name`. NOT REST.
- **Events API** — Slack POSTs events to your URL when things happen. Requires URL verification challenge.
- **Socket Mode** — WebSocket-based alternative to Events API. No public URL needed.
- **Block Kit** — JSON schema for rich UI in messages, modals, and Home tab.
- **Interactive Components** — Buttons, select menus, modals. Slack POSTs interaction payloads to your app.
- **Slash Commands** — `/command` invocations. Slack POSTs form data to your URL.

### Request/Response Pattern

```
POST https://slack.com/api/METHOD
Authorization: Bearer xoxb-TOKEN
Content-Type: application/json

Response: { "ok": true, "error": "...", ...fields }
```

**Always check `ok: true` before using response data.**

---

## 2. Authentication and Tokens

### Token Types

| Prefix | Name | Issued to | Use |
|---|---|---|---|
| `xoxb-` | Bot token | App's bot user | Most API calls; preferred |
| `xoxp-` | User token | Authorized user | Acting as a person; user-scoped calls |
| `xapp-` | App-level token | App (org-wide) | Socket Mode; `apps.connections.open` |
| `xwfp-` | Workflow token | Workflow step | 15-min expiry |
| *(service)* | Service token | Deno SDK apps only | Non-expiring; internal apps |

### OAuth 2.0 Flow

```
1. Redirect user to:
   https://slack.com/oauth/v2/authorize
     ?client_id=YOUR_CLIENT_ID
     &scope=chat:write,channels:read
     &redirect_uri=https://your-app.com/callback

2. Slack redirects back with ?code=...

3. Exchange code:
   POST https://slack.com/api/oauth.v2.access
   { client_id, client_secret, code, redirect_uri }

4. Response: { access_token: "xoxb-...", bot_user_id, team: { id, name } }
```

### Token Rotation

Opt in via App Settings → Manage Distribution → Rotate Tokens. Expiring tokens include `refresh_token`; call `tooling.tokens.rotate` before expiry. All tokens can be revoked with `auth.revoke`.

### Common Scopes

| Scope | Description |
|---|---|
| `chat:write` | Send messages as bot |
| `chat:write.public` | Send to any public channel without joining |
| `channels:read` | List public channels |
| `channels:history` | Read messages in public channels |
| `groups:history` | Read messages in private channels |
| `im:history` | Read DM messages |
| `users:read` | View user details |
| `reactions:write` | Add reactions |
| `files:write` | Upload files |
| `search:read` | Search messages/files |
| `canvases:write` | Create/update canvases |

---

## 3. Slack CLI Reference

Install: `curl -fsSL https://downloads.slack-edge.com/slack-cli/install.sh | bash`

```bash
# Auth
slack login / slack logout / slack auth list

# Project lifecycle
slack create my-app [--template slack-samples/bolt-js-starter-template]
slack run                  # Run locally with live reload + auto-tunnel
slack deploy               # Deploy to Slack's infrastructure (Deno apps)

# Triggers
slack trigger create / list / update / delete / info / access

# Datastores
slack datastore put --datastore my_store --item '{"id":"1","value":"test"}'
slack datastore get --datastore my_store --id 1
slack datastore query --datastore my_store --expression "#id = :val"
slack datastore bulk-put --datastore my_store --items-file items.json

# Env vars
slack env add MY_KEY MY_VALUE
slack env remove MY_KEY
slack env list

# Diagnostics
slack doctor                     # Check system requirements
slack activity                   # View app activity / event logs
slack activity --source "events" --level "error"
slack manifest validate
```

---

## 4. Web API

**Base URL:** `https://slack.com/api/`
**Auth:** `Authorization: Bearer <token>` header (never query string)

### Key API Method Families

```
# Conversations
conversations.list / info / history / replies / members
conversations.join / invite / open / create / archive

# Messages
chat.postMessage / update / delete / postEphemeral / getPermalink
chat.scheduleMessage / deleteScheduledMessage / scheduledMessages.list
chat.startStream / appendStream / stopStream   (AI streaming)

# Users
users.info / list / lookupByEmail / getPresence
users.profile.get / profile.set

# Files
files.upload / list / info / delete
files.getUploadURLExternal / completeUploadExternal   (v2 upload)

# Reactions
reactions.add / remove / get / list

# Search
search.messages / search.files / search.all

# Auth
auth.test / auth.revoke
apps.connections.open   (Socket Mode)
oauth.v2.access / oauth.v2.user.access
```

### Rate Limits

| Tier | Rate | Typical methods |
|---|---|---|
| Tier 1 | 1+ per minute | `channels.create`, `users.list` |
| Tier 2 | 20+ per minute | `users.info`, `conversations.info` |
| Tier 3 | 50+ per minute | `conversations.history`, `chat.update` |
| Tier 4 | 100+ per minute | `reactions.add`, `users.profile.get` |
| Special | 1/sec per channel | `chat.postMessage` |

On 429, Slack returns `Retry-After` header. Always implement exponential backoff.

### Error Handling Pattern

```javascript
const resp = await fetch('https://slack.com/api/chat.postMessage', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${SLACK_BOT_TOKEN}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({ channel, text, blocks })
});
const data = await resp.json();
if (!data.ok) throw new Error(`Slack API error: ${data.error}`);
```

### chat.postMessage — Key Arguments

```json
{
  "channel": "C1234567890",
  "text": "Fallback text",
  "blocks": [...],
  "thread_ts": "1234567890.123456",
  "reply_broadcast": false,
  "link_names": true,
  "unfurl_links": true
}
```

Response includes `ts` (unique message ID) and `channel`.

---

## 5. Events API

### Setup

1. App Config → Event Subscriptions → Enable Events
2. Set Request URL (must respond to verification challenge)
3. Subscribe to events (bot / workspace scopes)

### URL Verification Challenge

```javascript
app.post('/slack/events', (req, res) => {
  if (req.body.type === 'url_verification') {
    return res.json({ challenge: req.body.challenge });
  }
  res.sendStatus(200);  // always respond within 3 seconds; process async
});
```

### Common Bot Events

| Event | Fires when |
|---|---|
| `message` | Message posted in subscribed channel |
| `app_mention` | Bot is `@mentioned` |
| `app_home_opened` | User opens Home tab |
| `reaction_added` / `reaction_removed` | Emoji reaction changed |
| `member_joined_channel` | User joins channel |
| `file_shared` | File uploaded to channel |
| `tokens_revoked` | Tokens revoked (must clean up) |
| `app_uninstalled` | App uninstalled from workspace |

### Interaction Payloads

POSTed to your `interactivity_url`:

```json
{
  "type": "block_actions",
  "user": { "id": "U..." },
  "trigger_id": "...",
  "actions": [{ "action_id": "button_click", "type": "button", "value": "my_value" }]
}
```

`trigger_id` expires in 3 seconds — use immediately to open modals.

---

## 6. Socket Mode

Requirements: Enable Socket Mode in App Config; generate an App-Level Token (`xapp-`) with `connections:write` scope. App cannot be published to Slack Marketplace.

```javascript
// 1. Get WSS URL
const resp = await fetch('https://slack.com/api/apps.connections.open', {
  method: 'POST', headers: { 'Authorization': `Bearer ${XAPP_TOKEN}` }
});
const { url } = await resp.json();

// 2. Connect and ACK each event
const ws = new WebSocket(url);
ws.on('message', (raw) => {
  const envelope = JSON.parse(raw);
  ws.send(JSON.stringify({ envelope_id: envelope.envelope_id, payload: {} }));
  handleEvent(envelope.payload);  // process async after ACK
});

ws.on('close', () => reconnect());  // URL expires ~1 hour
```

**Multi-connection:** Up to 10 simultaneous WebSocket connections per app. All connections receive identical events.

---

## 7. Block Kit

### Blocks (Top-Level)

| Block type | Key fields | Limits |
|---|---|---|
| `section` | `text`, `fields`, `accessory` | |
| `header` | `text` (plain_text only) | |
| `divider` | — | |
| `image` | `image_url`, `alt_text`, `title` | |
| `actions` | `elements` | Up to 5 buttons/selects |
| `input` | `element`, `label`, `hint`, `optional` | Modals only |
| `context` | `elements` (text/image mix) | |
| `rich_text` | `elements` | |
| `video` | `video_url`, `thumbnail_url`, `alt_text` | |
| `context_actions` | `elements` (AI feedback) | 2025+ |

**Limits:** 50 blocks per message, 100 per modal/Home tab.

### Block Elements (Interactive)

| Element | Context |
|---|---|
| `button` | actions, accessory |
| `static_select` / `multi_static_select` | actions, input, accessory |
| `users_select` / `conversations_select` / `channels_select` | actions, input, accessory |
| `datepicker` / `timepicker` / `datetimepicker` | actions, input |
| `plain_text_input` / `number_input` / `url_text_input` | input |
| `radio_buttons` / `checkboxes` | actions, input, accessory |
| `rich_text_input` / `file_input` | input |
| `feedback_buttons` | context_actions (AI feedback, 2025+) |

### Slack Markdown (mrkdwn)

```
*bold*   _italic_   ~strikethrough~   `code`   ```code block```
> blockquote   :emoji_name:   @username   #channel
<URL|link text>   <!channel>   <!here>   <!everyone>
```

### Example: Rich Message Block

```json
{
  "blocks": [
    { "type": "header", "text": { "type": "plain_text", "text": "🚨 Alert: Disk 90% Full" } },
    {
      "type": "section",
      "text": { "type": "mrkdwn", "text": "*Server:* prod-db-01\n*Disk:* `/dev/sda1`\n*Usage:* 90.2%" },
      "accessory": {
        "type": "button",
        "text": { "type": "plain_text", "text": "View Dashboard" },
        "url": "https://grafana.example.com",
        "action_id": "view_dashboard"
      }
    },
    {
      "type": "actions",
      "elements": [
        { "type": "button", "text": { "type": "plain_text", "text": "Acknowledge" }, "style": "primary", "action_id": "acknowledge_alert" }
      ]
    },
    { "type": "divider" },
    { "type": "context", "elements": [{ "type": "mrkdwn", "text": "Alert fired at <!date^1234567890^{date_short} {time}|just now>" }] }
  ]
}
```

---

## 8. Modals and Views

```javascript
// Requires trigger_id from interaction payload (expires 3 seconds!)
await fetch('https://slack.com/api/views.open', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${BOT_TOKEN}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({
    trigger_id,
    view: {
      type: 'modal',
      callback_id: 'my_modal',
      title: { type: 'plain_text', text: 'My Form' },
      submit: { type: 'plain_text', text: 'Submit' },
      close: { type: 'plain_text', text: 'Cancel' },
      private_metadata: JSON.stringify({ sourceChannel: 'C123' }),
      blocks: [
        {
          type: 'input', block_id: 'name_block',
          label: { type: 'plain_text', text: 'Your name' },
          element: { type: 'plain_text_input', action_id: 'name_input' }
        }
      ]
    }
  })
});
```

**View stack operations:** `views.open` (requires trigger_id) → `views.push` → `views.update`. Stack limit: 3 views deep.

**Handling submission:**
```javascript
app.post('/slack/interactions', async (req, res) => {
  const payload = JSON.parse(req.body.payload);
  if (payload.type === 'view_submission' && payload.view.callback_id === 'my_modal') {
    const values = payload.view.state.values;
    res.json({});  // empty 200 closes modal
    // Or: res.json({ response_action: 'errors', errors: { name_block: 'Required' } });
  }
});
```

**Private metadata:** max 3000 chars, URL-encoded string. Use `JSON.stringify({})` to pass structured data.

---

## 9. Bolt SDK

### Bolt for JavaScript

```bash
npm install @slack/bolt
```

```javascript
const { App } = require('@slack/bolt');
const app = new App({
  token: process.env.SLACK_BOT_TOKEN,
  signingSecret: process.env.SLACK_SIGNING_SECRET,
  socketMode: true,                               // or HTTP mode (omit these two)
  appToken: process.env.SLACK_APP_TOKEN,
});

app.message('hello', async ({ message, say }) => {
  await say({ text: `Hey <@${message.user}>!` });
});

app.action('button_click', async ({ body, ack, say }) => {
  await ack();
  await say(`<@${body.user.id}> clicked the button!`);
});

app.command('/echo', async ({ command, ack, respond }) => {
  await ack();
  await respond(`You said: ${command.text}`);
});

app.view('my_modal', async ({ ack, body, view, client }) => {
  await ack();
  const values = view.state.values;
  await client.chat.postMessage({ channel: body.user.id, text: 'Got it!' });
});

(async () => await app.start(3000))();
```

**Required env vars:**
```bash
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=xxx...
SLACK_APP_TOKEN=xapp-...   # Socket Mode only
```

### Bolt for Python

```python
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

app = App(token=os.environ["SLACK_BOT_TOKEN"])

@app.message("hello")
def handle_hello(message, say):
    say(f"Hey there <@{message['user']}>!")

@app.action("button_click")
def handle_button(ack, body, say):
    ack()
    say(f"<@{body['user']['id']}> clicked!")

if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
```

---

## 10. Slack MCP Server

- **Transport:** JSON-RPC 2.0 over Streamable HTTP
- **Endpoint:** `https://mcp.slack.com/mcp`
- **Auth:** Confidential OAuth 2.0 (user tokens)
- **Availability:** Marketplace-published and internal apps only (unlisted apps prohibited)

### MCP Tools

| Tool | Rate Limit |
|---|---|
| Search messages & files | Special |
| Search users / channels | Tier 2: 20+/min |
| Send message | Special (1/sec per channel) |
| Read channel / thread | Tier 3: 50+/min |
| Create canvas / Update canvas | Tier 2–3 |
| Read user profile | Tier 4: 100+/min |

### Config

```json
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": ["-y", "@slack/mcp-server"],
      "env": {
        "SLACK_MCP_SSE_URL": "https://mcp.slack.com/mcp",
        "SLACK_CLIENT_ID": "YOUR_CLIENT_ID",
        "SLACK_CLIENT_SECRET": "YOUR_CLIENT_SECRET"
      }
    }
  }
}
```

Partner MCP clients: Claude.ai, Claude Code, Perplexity, Cursor.

---

## 11. Agents and AI Apps

Enable: App Settings → Agents & AI Apps → Toggle on.

### Assistant Threads API

```javascript
// Set thread status (loading indicator)
await client.assistant.threads.setStatus({
  channel_id: event.channel, thread_ts: event.thread_ts, status: 'Thinking...'
});

// Set suggested prompts
await client.assistant.threads.setSuggestedPrompts({
  channel_id: event.channel, thread_ts: event.thread_ts,
  prompts: [
    { title: 'Summarize', message: 'Summarize this channel' },
    { title: 'Action items', message: 'List action items from today' }
  ]
});
```

### LLM Streaming (chat.startStream / appendStream / stopStream)

```javascript
const { stream_ts } = await client.chat.startStream({ channel: channelId, thread_ts: threadTs });

// Append thinking step
await client.chat.appendStream({ channel: channelId, stream_ts, chunks: [{
  type: 'task_update', task_id: 'search', title: 'Searching...', status: 'in_progress'
}]});

// Append text
await client.chat.appendStream({ channel: channelId, stream_ts, chunks: [{
  type: 'markdown_text', text: 'Here is the answer...'
}]});

await client.chat.stopStream({ channel: channelId, stream_ts });
```

### Bolt SDK Streaming Helpers

```javascript
// JavaScript: sayStream
app.message('', async ({ message, sayStream }) => {
  const stream = await sayStream({ thread_ts: message.ts });
  await stream.appendTask({ task_id: 'thinking', title: 'Processing...', status: 'in_progress' });
  await stream.appendMarkdown('Result here.');
  await stream.stop();
});
```

```python
# Python: say_stream
@app.message("")
def handle_message(message, say_stream):
    stream = say_stream(thread_ts=message["ts"])
    stream.append_task(task_id="thinking", title="Processing...", status="in_progress")
    stream.append_markdown("Result here.")
    stream.stop()
```

### Key Events for Agents

| Event | Fires when |
|---|---|
| `assistant_thread_started` | User opens a new assistant thread |
| `assistant_thread_context_changed` | User switches channel context |
| `message` (in assistant thread) | User sends a message |

**Required scopes:** `assistant:write`, `chat:write`, `im:history`

---

## 12. Real-Time Search (RTS) API

GA February 2026. Allows real-time searches across Slack workspace data for AI agent RAG patterns without external data storage.

- **Availability:** Directory-published and internal apps only
- **Auth:** User token (`xoxp-`) required — bot tokens not supported
- **Use case:** AI agent RAG, context retrieval, real-time data freshness

Launch partners: Claude.ai, Google Agentspace, Dropbox Dash, Perplexity Enterprise, Notion AI.

---

## 13. Work Objects

GA October 2025. Transform static content from third-party services into interactive, dynamic experiences combining unfurls with a rich flexpane detail view.

### Implementation Flow

```
1. App posts message with eventAndEntityMetadata via chat.postMessage
2. Slack renders the Work Object unfurl in the message
3. User clicks unfurl → Slack fires entity_details_requested event
4. App calls entity.presentDetails with flexpane Block Kit content
5. Flexpane opens with interactive detail view
```

Docs: https://docs.slack.dev/messaging/work-objects

---

## 14. Common Recipes

### Robust API Call Helper

```javascript
async function slackCall(method, params, token) {
  const resp = await fetch(`https://slack.com/api/${method}`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (resp.status === 429) {
    const retryAfter = parseInt(resp.headers.get('Retry-After') || '1', 10);
    await new Promise(r => setTimeout(r, retryAfter * 1000));
    return slackCall(method, params, token);
  }
  const data = await resp.json();
  if (!data.ok) throw new Error(`Slack ${method} failed: ${data.error}`);
  return data;
}
```

### Paginate conversations.history

```javascript
async function getFullHistory(channel, token, oldest) {
  const messages = [];
  let cursor;
  do {
    const data = await slackCall('conversations.history', { channel, limit: 200, oldest, cursor }, token);
    messages.push(...data.messages);
    cursor = data.response_metadata?.next_cursor;
  } while (cursor);
  return messages;
}
```

### Find User by Email

```javascript
async function findUser(email, token) {
  const data = await slackCall('users.lookupByEmail', { email }, token);
  return data.user;
}
```

---

## 15. Deprecation and Migration Timeline

| Date | Change | Action Required |
|---|---|---|
| **March 31, 2025** | Legacy custom bots discontinued | Create new Slack apps; migrate to bot tokens |
| **September 1, 2025** | Slack CLI no longer bundles Deno | Install Deno separately; update CI scripts |
| **November 16, 2026** | Classic apps support ends | Migrate to granular bot tokens + new app model |

**Classic apps → Granular permissions:** Map each classic scope to its granular equivalent. New apps require OAuth with granular `xoxb-` tokens.

---

## 16. Sources

- [Slack Developer Docs](https://docs.slack.dev/)
- [Slack Web API Reference](https://api.slack.com/)
- [Slack CLI Docs](https://docs.slack.dev/tools/slack-cli/)
- [Slack MCP Server](https://docs.slack.dev/ai/slack-mcp-server/)
- [Agents & AI Apps](https://docs.slack.dev/ai/)
- [Work Objects](https://docs.slack.dev/messaging/work-objects)
- [RTS API](https://docs.slack.dev/apis/web-api/real-time-search-api/)
- [Changelog](https://docs.slack.dev/changelog/)

## 17. 2026 Q1–Q2 Platform Delta (added 2026-06-10)

Verified against the official changelog (docs.slack.dev/changelog) and Slack dev blog, accessed 2026-06-10. Confidence tags as elsewhere.

- **Slack MCP Server expanded** (2026-05-13): tool surface now 13 — added `add_reaction`, `create_conversation`, `list_channel_members`, `list_emoji`, `read_files`; per-app toggle via manifest `settings.is_mcp_enabled` (CLI 4.1.0). Directory-published or internal apps only. [HIGH]
- **Block Kit agent components**: Alert, Card, Carousel blocks (2026-04-16); `data table` block GA (2026-05-20); "Thinking Steps" streaming chunks (`task_card`/`plan`/url-source via `chat.startStream/appendStream/stopStream`, `chunks` + `task_display_mode` params, 2026-02-11); Work Object slugs/unfurls + Code block announced. [HIGH]
- **Agent Developer Kit / CLI 4.x** (2026-04-10+): `slack create agent` templates (Bolt JS/Python × Claude Agent SDK / OpenAI Agents SDK / Pydantic AI, MCP pre-wired); `slack env` commands, `slack docs search`, file-watch live reload; generic `slack api <method>` (4.1.0) and `--no-auth` (4.2.0, 2026-06-03); Bolt JS 4.7.x / Bolt Python 1.28.0 add `sayStream` + listener `setStatus`. [HIGH]
- **Auth deltas**: PKCE GA (2026-03-30) — public-client flag is one-way; custom-URI installs always receive rotating tokens; PKCE refresh tokens expire after 30 days; desktop redirects can't request bot scopes. Optional OAuth scopes GA (2026-03-16) via `oauth_config.scopes.bot_optional`/`user_optional` — handle `missing_scope`. `assistant.threads.setStatus` now prefers `chat:write`; `assistant:write` on that method will eventually be dropped (2026-03-05). [HIGH]
- **New Web API params** (2026-06-03): authorship (`icon_emoji`/`icon_url`/`username`) on `assistant.threads.setStatus` + `chat.startStream`; `highlight_type` on `files.completeUploadExternal`/`filesUploadV2`. [HIGH]
- **Events API**: Delayed Events retry (2026-02-05) replays events missed during app outages. [HIGH]
- **Rate limits**: the 1 req/min / 15-object `conversations.history`/`replies` limit for commercially distributed non-Marketplace apps reportedly extended to EXISTING unlisted installs on 2026-03-03, ending grandfathering (practitioner-corroborated; the live doc page wording lags — [MEDIUM]). Internal apps and Marketplace apps remain exempt.
- **SUPERSEDES §15 row**: the classic-app sunset (table above says Nov 16, 2026) was **paused indefinitely on 2025-12-08** — classic apps continue to work; no new ones can be created. [HIGH]
- **Deno SDK**: alive (2.15.2, 2026-02-26) but de-emphasized — agent templates are Bolt-only; Bolt is the strategic path. [MEDIUM]
- **Ecosystem sentiment** [MEDIUM]: prominent criticism (Fivetran "Anthropic, please make a new Slack"; HN 2026-06) that rate limits + RTS no-store/no-train terms wall customer data off from external AI; Marketplace listing is the only viable path for history-reading commercial apps.
