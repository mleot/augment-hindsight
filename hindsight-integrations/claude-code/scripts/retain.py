#!/usr/bin/env python3
"""Auto-retain hook for Stop event.

Port of: agent_end handler in Openclaw index.js
Adapted for code-agent hooks (ephemeral process, JSON stdin/stdout).
Supports Claude Code (transcript_path), Augment Code (_exchange), and
Cortex Code.

Flow:
  1. Read hook input from stdin
  2. Read conversation from transcript_path or _exchange
  3. Apply chunked retention logic (retainEveryNTurns + overlap window)
  4. Resolve API URL (external, existing local, or auto-start daemon)
  5. Derive bank ID and ensure mission
  6. Format transcript (strip memory tags, filter roles)
  7. POST to Hindsight retain API (async)

Exit codes:
  0 — always (graceful degradation on any error)
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
    slice_last_turns_by_user_boundary,
)
from lib.daemon import get_api_url
from lib.state import increment_turn_count


def read_transcript(transcript_path: str) -> list:
    """Read a JSONL transcript file and return list of message dicts.

    Claude Code transcript format nests messages:
      {type: "user", message: {role: "user", content: "..."}, uuid: "...", ...}
    Also supports flat format for testing:
      {role: "user", content: "..."}
    """
    if not transcript_path or not os.path.isfile(transcript_path):
        return []
    messages = []
    try:
        with open(transcript_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    # Claude Code nested format: {type: "user", message: {role, content}}
                    if entry.get("type") in ("user", "assistant"):
                        msg = entry.get("message", {})
                        if isinstance(msg, dict) and msg.get("role"):
                            messages.append(msg)
                    # Flat format (testing / future compatibility)
                    elif "role" in entry and "content" in entry:
                        messages.append(entry)
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return messages


def extract_messages_from_exchange(hook_input: dict) -> list:
    """Extract messages from Augment Code's _exchange field.

    Augment Code provides conversation content inline:
      {"_exchange": {"exchange": {"request_message": "...", "response_text": "..."}, ...}}
    """
    exchange_wrapper = hook_input.get("_exchange")
    if not isinstance(exchange_wrapper, dict):
        return []
    exchange = exchange_wrapper.get("exchange")
    if not isinstance(exchange, dict):
        return []
    messages = []
    request = exchange.get("request_message", "")
    if request:
        messages.append({"role": "user", "content": request})
    response = exchange.get("response_text", "")
    if response:
        messages.append({"role": "assistant", "content": response})
    return messages


def get_messages(hook_input: dict, config: dict) -> list:
    """Get conversation messages from hook input, trying all known formats.

    Priority: transcript_path (Claude Code) > _exchange (Augment Code) > empty.
    """
    transcript_path = hook_input.get("transcript_path", "")
    if transcript_path:
        messages = read_transcript(transcript_path)
        if messages:
            debug_log(config, f"Read {len(messages)} messages from transcript file")
            return messages

    messages = extract_messages_from_exchange(hook_input)
    if messages:
        debug_log(config, f"Read {len(messages)} messages from _exchange")
        return messages

    debug_log(config, "No messages found in transcript_path or _exchange")
    return []


def main():
    config = load_config()

    if not config.get("autoRetain"):
        debug_log(config, "Auto-retain disabled, exiting")
        return

    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        print("[Hindsight] Failed to read hook input", file=sys.stderr)
        return

    debug_log(config, f"Stop hook input keys: {list(hook_input.keys())}")

    session_id = hook_input.get("session_id") or hook_input.get("conversation_id") or "unknown"

    # Get messages from whichever source the agent provides
    all_messages = get_messages(hook_input, config)
    if not all_messages:
        return

    # Detect whether we're using _exchange (single-turn inline data) vs
    # transcript_path (full session history).  With _exchange each hook
    # invocation only sees the current turn, so skipping turns means
    # permanently losing data.  Force retainEveryNTurns=1 in that case.
    has_transcript = bool(hook_input.get("transcript_path"))
    using_exchange = not has_transcript and "_exchange" in hook_input

    # Retention mode: full session (default) or chunked (legacy)
    retain_mode = config.get("retainMode", "full-session")
    retain_every_n = max(1, config.get("retainEveryNTurns", 1))
    if using_exchange and retain_every_n > 1:
        debug_log(config, f"_exchange mode: overriding retainEveryNTurns {retain_every_n} -> 1 (no transcript history)")
        retain_every_n = 1
    retain_full_window = False
    messages_to_retain = all_messages

    # Respect retainEveryNTurns in both modes
    if retain_every_n > 1:
        turn_count = increment_turn_count(session_id)
        if turn_count % retain_every_n != 0:
            next_at = ((turn_count // retain_every_n) + 1) * retain_every_n
            debug_log(config, f"Turn {turn_count}/{retain_every_n}, skipping retain (next at turn {next_at})")
            return

    if retain_mode == "chunked" and retain_every_n > 1:
        # Sliding window: N turns + configured overlap
        overlap_turns = config.get("retainOverlapTurns", 0)
        window_turns = retain_every_n + overlap_turns
        messages_to_retain = slice_last_turns_by_user_boundary(all_messages, window_turns)
        retain_full_window = True
        debug_log(
            config,
            f"Chunked retain firing (window: {window_turns} turns, {len(messages_to_retain)} messages)",
        )
    else:
        # Full session mode: retain all messages, always as full window
        retain_full_window = True
        debug_log(config, f"Full session retain: {len(all_messages)} messages")

    # Format transcript
    retain_roles = config.get("retainRoles", ["user", "assistant"])
    include_tool_calls = config.get("retainToolCalls", True)
    transcript, message_count = prepare_retention_transcript(
        messages_to_retain, retain_roles, retain_full_window, include_tool_calls=include_tool_calls
    )

    if not transcript:
        debug_log(config, "Empty transcript after formatting, skipping retain")
        return

    # Resolve API URL
    def _dbg(*a):
        debug_log(config, *a)

    try:
        api_url = get_api_url(config, debug_fn=_dbg, allow_daemon_start=True)
    except RuntimeError as e:
        print(f"[Hindsight] {e}", file=sys.stderr)
        return

    api_token = config.get("hindsightApiToken")
    try:
        client = HindsightClient(api_url, api_token)
    except ValueError as e:
        print(f"[Hindsight] Invalid API URL: {e}", file=sys.stderr)
        return

    # Derive bank ID and ensure mission
    bank_id = derive_bank_id(hook_input, config)
    ensure_bank_mission(client, bank_id, config, debug_fn=_dbg)

    # Document ID: use session_id so the same session always upserts the same document.
    # In chunked mode, append timestamp to create distinct documents per chunk.
    if retain_mode == "chunked" and retain_every_n > 1:
        document_id = f"{session_id}-{int(time.time() * 1000)}"
    else:
        document_id = session_id

    # Resolve template variables in tags and metadata.
    # Supported variables: {session_id}, {bank_id}, {timestamp}
    template_vars = {
        "session_id": session_id,
        "bank_id": bank_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    def _resolve_template(value: str) -> str:
        for k, v in template_vars.items():
            value = value.replace(f"{{{k}}}", v)
        return value

    # Tags from config with template resolution
    raw_tags = config.get("retainTags", [])
    tags = [_resolve_template(t) for t in raw_tags] if raw_tags else None

    # Metadata: merge built-in defaults with user-configured extras
    metadata = {
        "retained_at": template_vars["timestamp"],
        "message_count": str(message_count),
        "session_id": session_id,
    }
    for k, v in config.get("retainMetadata", {}).items():
        metadata[k] = _resolve_template(str(v))

    debug_log(
        config, f"Retaining to bank '{bank_id}', doc '{document_id}', {message_count} messages, {len(transcript)} chars"
    )
    if tags:
        debug_log(config, f"Tags: {tags}")

    # POST to Hindsight retain API
    try:
        response = client.retain(
            bank_id=bank_id,
            content=transcript,
            document_id=document_id,
            context=config.get("retainContext", "claude-code"),
            metadata=metadata,
            tags=tags,
            timeout=15,
        )
        debug_log(config, f"Retain response: {json.dumps(response)[:200]}")
    except Exception as e:
        print(f"[Hindsight] Retain failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[Hindsight] Unexpected error in retain: {e}", file=sys.stderr)
        try:
            from lib.config import load_config

            sys.exit(2 if load_config().get("debug") else 0)
        except Exception:
            sys.exit(0)
