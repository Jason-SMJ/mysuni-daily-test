# Daily Check Precheck Spec

## Purpose
- Daily check automation using Playwright + Azure OpenAI Vision
- Slack DM notification for validation result (text/file)

## Required Accounts / Access
- Playwright test account with Career permission
- Azure OpenAI deployment access (`vision_deployment`)
- Slack app bot token and DM target (`dm_user_id` or `dm_email`)

## Slack Required Scopes
- `chat:write`
- `files:write`
- `users:read.email` (if email lookup is used)
- `conversations:write` or `im:write` (depending on workspace policy)

## Baseline Image Policy
- Baseline images are optional but recommended for comparison mode.
- Place baseline files under `baseline/career_profile/`.
- File naming follows `tests/specs/daily_check_spec.py` `reference_image` values.

## Selector/Action Policy
- Selector priority:
  1. `data-testid`
  2. semantic selector (visible text/label/button)
  3. structural selector (CSS structure)
- Context expansion order:
  1. main document
  2. iframe context
  3. JS fallback in main
  4. JS fallback in iframe

## Popup Policy
- Open popup using +/edit button
- Capture screenshot after popup is visible
- Close popup (`닫기/취소/X`) and `Escape` fallback
- Browser dialog is accepted automatically when detected
