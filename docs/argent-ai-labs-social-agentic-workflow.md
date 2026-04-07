# Argent AI Labs — Agentic Social Media Content Workflow

## A) MVP Workflow (Build This First)

### 1) MVP Architecture (practical + production-safe)

**Goal:** generate, approve, schedule, and publish content to Instagram, X, and Facebook with traceability.

**Core modules (separated):**
1. **Intake Module**: receives content input (topic, service, case study, raw script, transcript, media folder ref).
2. **Generation Module**: OpenAI creates platform-specific drafts and content variants.
3. **Approval Module**: human-in-the-loop toggle (`manual_approval=true|false`).
4. **Publishing Module**: posts using supported APIs/connectors.
5. **Logging Module**: writes all states to Google Sheets/Airtable.
6. **Reliability Module**: retry + failover + notifications.

### 2) Recommended MVP Stack

- **Orchestrator**: n8n (self-hosted recommended).
- **AI**: OpenAI API (single model for MVP + structured output mode).
- **Queue/DB**: Google Sheets (fastest MVP) or Airtable.
- **Storage**: Google Drive/Dropbox/S3 for media asset URLs.
- **Notifications**: Slack (or email fallback).
- **Scheduling**: n8n Cron + queue table.

### 3) Platform publishing reality (important)

- **Facebook Pages**: direct publishing is realistic via Meta Graph API.
- **Instagram Business**: direct publishing is realistic (business account linked to Facebook Page via Graph API).
- **X / Twitter**: direct publishing is possible via X API credentials and app permissions; setup is stricter and plan-dependent.
- If any credential/app scope is missing, workflow should move item to `NEEDS_MANUAL_POST` and generate final copy + media package URL.

### 4) MVP node-by-node design (single workflow)

1. **Trigger (Webhook/Cron/Manual Trigger)**
2. **Set Config** (manual approval flag, autopost flag, platform toggles)
3. **Normalize Input (Function)**
4. **Classify Input + Best Format (OpenAI)**
5. **Parse AI JSON (Function)**
6. **Generate Content Plan (OpenAI)**
7. **Generate Platform Captions (OpenAI)**
8. **Quality Gate (OpenAI self-critique)**
9. **If Weak Hooks? (IF node)**
10. **Regenerate Hooks (OpenAI)**
11. **Deduplicate Check (Sheets lookup by fingerprint)**
12. **If Duplicate -> regenerate angle OR skip**
13. **Write Draft to Queue (Sheets/Airtable)**
14. **Approval Router (IF manual approval?)**
15. **Manual Approval (Slack approval link or status update in sheet)**
16. **Scheduler (wait until scheduled datetime)**
17. **Publish Router (Switch by platform)**
18. **Publish Facebook**
19. **Publish Instagram**
20. **Publish X**
21. **Capture Post IDs (merge)**
22. **Update Queue Status = PUBLISHED/FAILED/PARTIAL**
23. **Notify result to Slack/Email**
24. **Error Trigger workflow for global failures**

### 5) MVP decision logic

- Input classification decides preferred content type:
  - transcript/case study -> reel or carousel
  - service/offer -> static + authority text thread
  - client result -> authority text + proof carousel
  - raw script -> short-form video + teaser text post
- If confidence < threshold, create 2 formats and queue both.

---

## B) Advanced Agentic Workflow (Version 2)

### 1) Advanced architecture (modular workflows)

Use separate n8n workflows for maintainability:

1. **WF-01 Intake & Enrichment**
2. **WF-02 Strategy Planner (weekly mix balancer)**
3. **WF-03 Content Generator**
4. **WF-04 Approval Orchestrator**
5. **WF-05 Publisher**
6. **WF-06 Retry + Recovery**
7. **WF-07 Analytics Feedback Loop**

### 2) Agentic behaviors implemented

- **Content Type Agent**: chooses reel/carousel/static/text authority post.
- **Platform Voice Agent**: creates per-platform tone and caption structure.
- **Quality Agent**: detects weak hooks, generic phrasing, repetitive syntax.
- **Diversity Agent**: prevents repetitive angles and enforces weekly mix quotas.
- **Risk Agent**: flags unverifiable claims and strips fake social proof.

### 3) Weekly mix balancer

Set weekly target distribution (editable in config table):
- 35% educational
- 25% authority/proof
- 20% contrarian insight
- 20% offer/CTA

If category exceeds quota, planner reassigns next post angle before generation.

### 4) Advanced add-ons (plug-in modules)

- AI image generation module (optional)
- Script-to-voiceover module
- Auto short-form edit pipeline (e.g., via external video API)
- Analytics-driven prompt tuning (top hooks feed back into prompt memory)

---

## C) n8n Implementation Details

### 1) Environment variables

Use n8n environment or credential store; never hardcode.

- `OPENAI_API_KEY`
- `META_APP_ID`
- `META_APP_SECRET`
- `META_PAGE_ACCESS_TOKEN`
- `META_IG_BUSINESS_ID`
- `X_API_KEY`
- `X_API_SECRET`
- `X_ACCESS_TOKEN`
- `X_ACCESS_TOKEN_SECRET`
- `SLACK_WEBHOOK_URL`
- `GOOGLE_SHEETS_CREDENTIAL_ID` (or Airtable vars)
- `DEFAULT_TIMEZONE`

### 2) Queue schema (Google Sheets / Airtable)

**Table: `content_queue`**
- `id` (uuid)
- `created_at`
- `input_type`
- `input_source`
- `topic`
- `content_angle`
- `content_type` (reel/carousel/static/text)
- `platform`
- `title`
- `hook`
- `caption`
- `cta`
- `hashtags`
- `thumbnail_text`
- `media_urls`
- `fingerprint`
- `approval_mode` (manual/auto)
- `approval_status` (pending/approved/rejected)
- `status` (draft/scheduled/publishing/published/failed/needs_manual_post)
- `scheduled_at`
- `published_at`
- `external_post_id`
- `retry_count`
- `failure_reason`
- `run_id`

**Table: `content_metrics`** (advanced)
- `queue_id`
- `platform`
- `likes`
- `comments`
- `shares`
- `saves`
- `clicks`
- `impressions`
- `engagement_rate`
- `captured_at`

### 3) Retry + fallback policy

- Retry on transient API errors (429/5xx/timeouts): exponential backoff (1m, 5m, 20m).
- Max retries default: 3.
- On permanent 4xx/auth errors: no retry, mark failed and notify.
- On posting unsupported for platform/account state:
  - set `status=needs_manual_post`
  - package final caption + media URL + recommended posting window
  - send Slack alert with one-click copy block.

### 4) Approval flow logic

- `approval_mode=manual`: queue enters `pending_approval`, notify Slack/email.
- Approver can set row status to `approved` or `rejected`.
- Cron checker publishes approved items at `scheduled_at`.
- `approval_mode=auto`: skip manual gate and schedule immediately.

### 5) Posting flow logic

For each queue row due now:
1. Lock row (`status=publishing`).
2. Route by platform.
3. Call platform node/API.
4. Save `external_post_id` + `published_at`.
5. If one platform fails in multi-platform batch, store partial status and continue others.

### 6) Duplicate prevention logic

Fingerprint formula:
`SHA256(lower(topic + '|' + angle + '|' + primary_hook + '|' + platform))`

Before inserting draft:
- lookup fingerprints in last 45 days.
- if duplicate: regenerate angle/hook once.
- if still duplicate: mark `skipped_duplicate`.

### 7) Folder structure (scalable)

```text
argent-social-agent/
  n8n/
    workflows/
      mvp_social_pipeline.json
      adv_intake_enrichment.json
      adv_strategy_planner.json
      adv_content_generator.json
      adv_approval_orchestrator.json
      adv_publisher.json
      adv_retry_recovery.json
      adv_analytics_loop.json
    credentials/
      README.md
  prompts/
    classify_input.txt
    generate_plan.txt
    generate_platform_copy.txt
    quality_gate.txt
    regenerate_hooks.txt
  helpers/
    function_nodes.js
  docs/
    setup.md
    troubleshooting.md
    content_guidelines.md
```

---

## D) Exact prompts for each AI node

### Prompt 1 — Input Classification (`classify_input`)

```text
SYSTEM:
You are the Content Strategy Agent for Argent AI Labs.
Return STRICT JSON only.
Never fabricate client outcomes.

USER:
Brand context:
- Brand: Argent AI Labs
- Audience: SMB owners/operators interested in AI automation
- Tone: modern, sharp, persuasive, non-generic, human

Input payload:
{{ $json.input_payload }}

Tasks:
1) Classify input_type into one of: topic_idea, business_service, case_study, client_result, raw_script, transcript, media_folder.
2) Choose best primary content_type: reel, carousel, static, authority_text.
3) Choose secondary content_type.
4) Provide confidence_score 0-1.
5) Extract 3 possible content angles.
6) Flag risk if claims are unverifiable.

Return JSON schema:
{
  "input_type": "...",
  "primary_content_type": "...",
  "secondary_content_type": "...",
  "confidence_score": 0.0,
  "angles": ["...", "...", "..."],
  "risk_flags": ["..."],
  "notes": "..."
}
```

### Prompt 2 — Content Plan Generator (`generate_plan`)

```text
SYSTEM:
You are a senior social strategist.
Return STRICT JSON only.
Avoid fluff, clichés, and obvious AI language.

USER:
Create a one-week micro content plan from this input:
{{ $json.classification }}

Constraints:
- Mix categories: educational, authority, contrarian, offer.
- No fake stories/results.
- Focus on actionable business value.
- Keep voice concise and premium.

Return JSON:
{
  "posts": [
    {
      "day": "Mon",
      "category": "educational",
      "platforms": ["instagram","x","facebook"],
      "content_type": "carousel",
      "title": "...",
      "core_angle": "...",
      "proof_point": "...",
      "cta_goal": "lead_generation"
    }
  ]
}
```

### Prompt 3 — Platform Copy Generator (`generate_platform_copy`)

```text
SYSTEM:
You create platform-native social copy for Argent AI Labs.
Return STRICT JSON only.
No repetitive openings. No robotic transitions. No spam hashtags.

USER:
Generate copy for this post object:
{{ $json.post }}

Rules:
- Instagram: hook + short narrative + CTA + 3-6 relevant hashtags.
- X: concise authority post/thread opener, high signal, no fluff.
- Facebook: clearer context paragraph + practical takeaway + CTA.
- Include thumbnail/cover text (max 6 words).
- Include 3 hook variants ranked strongest-first.

Return JSON:
{
  "instagram": {
    "title": "...",
    "hooks": ["...","...","..."],
    "caption": "...",
    "cta": "...",
    "hashtags": ["..."],
    "thumbnail_text": "..."
  },
  "x": { "title": "...", "hooks": ["..."], "caption": "...", "cta": "...", "hashtags": ["..."], "thumbnail_text": "..." },
  "facebook": { "title": "...", "hooks": ["..."], "caption": "...", "cta": "...", "hashtags": ["..."], "thumbnail_text": "..." }
}
```

### Prompt 4 — Quality Gate (`quality_gate`)

```text
SYSTEM:
You are a strict editorial QA agent. Return STRICT JSON only.

USER:
Evaluate this generated copy:
{{ $json.generated_copy }}

Score each platform 0-100 for:
- hook_strength
- specificity
- human_naturalness
- non_repetitiveness
- business_value

If any score < 75, provide concrete rewrite instructions.
Return:
{
  "pass": true,
  "scores": {
    "instagram": {"hook_strength": 0, "specificity": 0, "human_naturalness": 0, "non_repetitiveness": 0, "business_value": 0},
    "x": {...},
    "facebook": {...}
  },
  "rewrite_required": false,
  "rewrite_instructions": ["..."]
}
```

### Prompt 5 — Hook Regenerator (`regenerate_hooks`)

```text
SYSTEM:
Return STRICT JSON only.
You rewrite weak hooks into sharp, specific, non-hype business hooks.

USER:
Original hooks:
{{ $json.weak_hooks }}
Context:
{{ $json.context }}

Generate 5 stronger hook options per platform.
Output JSON:
{
  "instagram": ["..."],
  "x": ["..."],
  "facebook": ["..."]
}
```

---

## E) n8n JSON / pseudo-JSON (import starter)

> Full import-ready examples are provided in `/n8n/mvp_social_pipeline.json` and `/n8n/advanced_agentic_master.json`.

### MVP pseudo-JSON flow map

```json
{
  "name": "MVP - Argent Social Pipeline",
  "nodes": [
    {"name": "Webhook Intake", "type": "n8n-nodes-base.webhook"},
    {"name": "Set Config", "type": "n8n-nodes-base.set"},
    {"name": "Normalize Input", "type": "n8n-nodes-base.function"},
    {"name": "OpenAI Classify", "type": "n8n-nodes-base.httpRequest"},
    {"name": "Parse Classification", "type": "n8n-nodes-base.function"},
    {"name": "OpenAI Generate Plan", "type": "n8n-nodes-base.httpRequest"},
    {"name": "Split Posts", "type": "n8n-nodes-base.itemLists"},
    {"name": "OpenAI Platform Copy", "type": "n8n-nodes-base.httpRequest"},
    {"name": "OpenAI Quality Gate", "type": "n8n-nodes-base.httpRequest"},
    {"name": "IF Needs Rewrite", "type": "n8n-nodes-base.if"},
    {"name": "OpenAI Regenerate Hooks", "type": "n8n-nodes-base.httpRequest"},
    {"name": "Build Fingerprint", "type": "n8n-nodes-base.function"},
    {"name": "Sheet Lookup Duplicate", "type": "n8n-nodes-base.googleSheets"},
    {"name": "IF Duplicate", "type": "n8n-nodes-base.if"},
    {"name": "Sheet Insert Queue", "type": "n8n-nodes-base.googleSheets"},
    {"name": "IF Manual Approval", "type": "n8n-nodes-base.if"},
    {"name": "Slack Approval Notify", "type": "n8n-nodes-base.slack"},
    {"name": "Wait Until Schedule", "type": "n8n-nodes-base.wait"},
    {"name": "Switch Platform", "type": "n8n-nodes-base.switch"},
    {"name": "Publish Facebook", "type": "n8n-nodes-base.httpRequest"},
    {"name": "Publish Instagram", "type": "n8n-nodes-base.httpRequest"},
    {"name": "Publish X", "type": "n8n-nodes-base.httpRequest"},
    {"name": "Update Queue Status", "type": "n8n-nodes-base.googleSheets"},
    {"name": "Slack Result Notify", "type": "n8n-nodes-base.slack"}
  ]
}
```

### Advanced workflow orchestration

- Master scheduler triggers sub-workflows with `Execute Workflow` nodes.
- Each sub-workflow returns typed payloads (`workflowData`), then gets persisted.
- Retry workflow consumes failed rows and replays publish attempts by `queue_id`.

---

## Step-by-step setup

1. Create Google Sheet with `content_queue` schema.
2. Create n8n credentials: OpenAI HTTP, Google Sheets OAuth2, Slack, Meta/X HTTP auth.
3. Import MVP workflow JSON.
4. Set environment variables in n8n deployment.
5. Test with one `topic_idea` webhook payload.
6. Enable manual approval mode first.
7. Validate post IDs and logs.
8. Turn on auto-post only after 10+ successful scheduled runs.
9. Import advanced workflows and route from master scheduler.

---

## Testing checklist

1. Intake accepts all input types.
2. Classification returns strict JSON (no markdown wrappers).
3. Captions differ by platform.
4. Weak hooks trigger regeneration path.
5. Duplicate detection prevents repeated angles.
6. Manual approval blocks publishing until approved.
7. Auto mode publishes at schedule time.
8. Failed publish increments retry count.
9. Retry backoff behaves as configured.
10. Failure alerts include queue id + reason.
11. Partial failure preserves successful platform post IDs.
12. Queue row status transitions are consistent.

---

## Common errors and fixes

- **Invalid JSON from LLM**: enforce `response_format=json_schema` and add parser guard Function node.
- **Instagram publish fails**: verify business account linkage and required permissions.
- **X 403/401**: verify app scopes, user auth level, and posting permission.
- **Meta token expires**: add token refresh routine and alert before expiry.
- **Duplicate false positives**: include platform + angle in fingerprint input.
- **Rate limits**: throttle publish node and use queued retries.

---

## Minimal webhook payload example

```json
{
  "input_payload": {
    "type": "case_study",
    "topic": "How we reduced lead response time using AI routing",
    "raw_notes": "Before: 6 hours average. After automation: 12 minutes average.",
    "media_urls": ["https://.../before-after.png"],
    "desired_platforms": ["instagram", "x", "facebook"],
    "approval_mode": "manual",
    "scheduled_at": "2026-04-10T14:00:00Z"
  }
}
```
