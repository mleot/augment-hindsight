#!/usr/bin/env python3
"""SessionEnd hook: force final retention + daemon cleanup.

Enhanced version that ensures all conversation messages are retained
before session terminates, even if retainEveryNTurns threshold wasn't met.

This provides a safety net to prevent memory loss on early shutdown.

Flow:
  1. Force a final retain (ignoring retainEveryNTurns)
  2. Stop daemon if auto-started

Port of: Openclaw's service.stop() in index.js + final flush
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.bank import derive_bank_id, ensure_bank_mission
from lib.client import HindsightClient
from lib.config import debug_log, load_config
from lib.content import (
    prepare_retention_transcript,
    read_augment_transcript,
    read_cortex_transcript,
)
from lib.daemon import get_api_url, stop_daemon


def read_transcript(transcript_path: str) -> list:
    """Read a JSONL transcript file and return list of message dicts."""
    if not transcript_path or not os.path.isfile(transcript_path):
        return []

    messages = []
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line)
                # Claude Code nests messages: {type, message: {role, content}, ...}
                if "message" in entry:
                    messages.append(entry["message"])
                # Flat format: {role, content}
                elif "role" in entry:
                    messages.append(entry)
    except Exception as e:
        print(f"[Hindsight] Error reading transcript: {e}", file=sys.stderr)
        return []

    return messages


def extract_messages_from_exchange(hook_input: dict) -> list:
    """Extract messages from _exchange field (Augment single-turn format)."""
    exchange = hook_input.get("_exchange", {})
    messages = []
    
    user_msg = exchange.get("user_request")
    if user_msg:
        messages.append({"role": "user", "content": user_msg})
    
    assistant_msg = exchange.get("agent_response")
    if assistant_msg:
        messages.append({"role": "assistant", "content": assistant_msg})
    
    return messages


def get_messages(hook_input: dict, config: dict) -> list:
    """Get all messages from whatever source is available."""
    # Try transcript file first (Claude Code)
    transcript_path = hook_input.get("transcript_path", "")
    if transcript_path:
        messages = read_transcript(transcript_path)
        if messages:
            return messages

    # Try Cortex history file
    messages = read_cortex_transcript(hook_input)
    if messages:
        return messages

    # Try Augment session file
    messages = read_augment_transcript(hook_input)
    if messages:
        return messages

    # Fallback: current turn from _exchange
    return extract_messages_from_exchange(hook_input)


def force_final_retain(hook_input: dict, config: dict):
    """Force a final retention of all session messages, ignoring retainEveryNTurns."""
    
    if not config.get("autoRetain"):
        debug_log(config, "Auto-retain disabled, skipping final retention")
        return

    session_id = hook_input.get("session_id") or hook_input.get("conversation_id") or "unknown"
    
    # Get all messages
    all_messages = get_messages(hook_input, config)
    if not all_messages:
        debug_log(config, "No messages to retain in SessionEnd")
        return

    debug_log(config, f"SessionEnd: forcing final retention of {len(all_messages)} messages")

    # Format transcript
    retain_roles = config.get("retainRoles", ["user", "assistant"])
    include_tool_calls = config.get("retainToolCalls", True)
    transcript, message_count = prepare_retention_transcript(
        all_messages, retain_roles, retain_full_window=True, include_tool_calls=include_tool_calls
    )

    if not transcript:
        debug_log(config, "Empty transcript after formatting")
        return

    # Resolve API URL
    def _dbg(*a):
        debug_log(config, *a)

    try:
        api_url = get_api_url(config, debug_fn=_dbg, allow_daemon_start=False)  # Don't start daemon on shutdown
    except RuntimeError as e:
        print(f"[Hindsight] SessionEnd: {e}", file=sys.stderr)
        return

    api_token = config.get("hindsightApiToken")
    try:
        client = HindsightClient(api_url, api_token)
    except ValueError as e:
        print(f"[Hindsight] SessionEnd: Invalid API URL: {e}", file=sys.stderr)
        return

    # Derive bank ID
    bank_id = derive_bank_id(hook_input, config)
    
    # Document ID: use session_id for full-session upsert
    document_id = session_id

    # Prepare metadata
    template_vars = {
        "session_id": session_id,
        "bank_id": bank_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    metadata = {
        "retained_at": template_vars["timestamp"],
        "message_count": str(message_count),
        "session_id": session_id,
        "final_retention": "true",  # Flag this as the final shutdown retention
    }

    # POST to Hindsight
    try:
        response = client.retain(
            bank_id=bank_id,
            content=transcript,
            document_id=document_id,
            context=config.get("retainContext", "augment-code"),
            metadata=metadata,
            tags=config.get("retainTags", []),
            timeout=15,
        )
        debug_log(config, f"SessionEnd retain successful: {json.dumps(response)[:100]}")
    except Exception as e:
        print(f"[Hindsight] SessionEnd retain failed: {e}", file=sys.stderr)


def main():
    config = load_config()

    # Consume stdin
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        hook_input = {}

    reason = hook_input.get('reason', 'unknown')
    debug_log(config, f"SessionEnd hook, reason: {reason}")

    # 1. Force final retention before cleanup
    force_final_retain(hook_input, config)

    # 2. Stop daemon if we started it
    def _dbg(*a):
        debug_log(config, *a)

    stop_daemon(config, debug_fn=_dbg)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[Hindsight] SessionEnd error: {e}", file=sys.stderr)
        sys.exit(0)
