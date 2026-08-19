---
name: bot-and-integrations-builder
description: "Use when building Telegram bots, Discord bots, WhatsApp bots, Slack bots, webhooks, or third-party API integrations with resilience and retry logic."
---

# Bot & Integrations Builder Superpower

Build reliable, feature-rich conversational bots and webhooks with state management, graceful error recovery, and interactive menus.

## Architecture

1. **Telegram Bots**:
   - Polling vs Webhook modes.
   - Command handlers (`/start`, `/help`, `/status`), custom inline keyboards, and state machines (ConversationHandler).
   - Async execution using `python-telegram-bot` or lightweight raw HTTP API calls.
2. **Discord Bots**:
   - Slash commands (`@tree.command`) and interaction responses.
   - Event listeners (`on_ready`, `on_message`, `on_error`).
3. **Webhook Servers**:
   - HMAC signature verification for GitHub / Stripe / Telegram webhooks.
   - Rapid 200 OK acknowledgment with asynchronous background task processing.
4. **Resilience**:
   - Automatic reconnect on network dropouts.
   - Long-polling heartbeat monitoring.

## Resource Reference

Read `bot-boilerplates.md`:
`ACTION: skill INPUT: {"name": "bot-and-integrations-builder", "resource": "bot-boilerplates.md"}`
