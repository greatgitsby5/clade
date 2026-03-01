#!/usr/bin/env python3
"""
Parley — Memory sync through conversation.

Two AI agent memory stores walk in. A local LLM reconciles them.
No protocol. No schema agreement. Just conversation.
"""

import argparse
import json
import sys
import os
import importlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import ollama
except ImportError:
    print("Ollama Python client not found. Install it:")
    print("  pip install ollama")
    sys.exit(1)

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# ── Defaults ──────────────────────────────────────────────────

DEFAULT_MODEL = "llama3.1:8b"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
CHUNK_SIZE = 40  # memories per LLM call before chunking

BANNER = """
╔══════════════════════════════════════════════╗
║  PARLEY — Memory Sync Through Conversation   ║
╚══════════════════════════════════════════════╝"""


# ── Config ────────────────────────────────────────────────────

def load_config() -> dict:
    """Load parley.yaml if it exists."""
    config = {
        "model": DEFAULT_MODEL,
        "ollama_url": DEFAULT_OLLAMA_URL,
        "auto_accept_new": True,
        "auto_merge_duplicates": True,
        "require_review_conflicts": True,
        "redact_patterns": ["password", "api_key", "secret", "ssn", "credit card"],
        "save_conversations": True,
        "log_format": "markdown",
    }
    config_path = Path("parley.yaml")
    if config_path.exists() and HAS_YAML:
        with open(config_path) as f:
            user_config = yaml.safe_load(f) or {}
            config.update(user_config)
    return config


# ── Memory Store I/O ──────────────────────────────────────────

class MemoryAdapter:
    """Base adapter. Override for custom formats."""

    def read(self, path: str) -> list[dict]:
        raise NotImplementedError

    def write(self, path: str, memories: list[dict]):
        raise NotImplementedError


class JSONAdapter(MemoryAdapter):
    """Default: reads/writes JSON arrays of memory objects."""

    def read(self, path: str) -> list[dict]:
        with open(path) as f:
            data = json.load(f)
        # Handle both arrays and objects with a "memories" key
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "memories" in data:
            return data["memories"]
        # Single object → wrap in list
        if isinstance(data, dict):
            return [data]
        return []

    def write(self, path: str, memories: list[dict]):
        with open(path, "w") as f:
            json.dump(memories, f, indent=2, default=str)


class PlainTextAdapter(MemoryAdapter):
    """One memory per line, plain text."""

    def read(self, path: str) -> list[dict]:
        with open(path) as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        return [{"content": line, "type": "fact"} for line in lines]

    def write(self, path: str, memories: list[dict]):
        with open(path, "w") as f:
            for m in memories:
                f.write(m.get("content", str(m)) + "\n")


def get_adapter(path: str, custom_adapter: Optional[str] = None) -> MemoryAdapter:
    """Resolve the right adapter for a store."""
    if custom_adapter:
        module_path, class_name = custom_adapter.rsplit(".", 1)
        module = importlib.import_module(module_path)
        adapter_class = getattr(module, class_name)
        return adapter_class()

    ext = Path(path).suffix.lower()
    if ext == ".json":
        return JSONAdapter()
    elif ext in (".txt", ".md"):
        return PlainTextAdapter()
    else:
        print(f"Unknown file format: {ext}. Trying JSON.")
        return JSONAdapter()


# ── Redaction ─────────────────────────────────────────────────

def redact_memories(memories: list[dict], patterns: list[str]) -> list[dict]:
    """Remove memories that match redaction patterns."""
    clean = []
    for m in memories:
        content = m.get("content", str(m)).lower()
        if not any(p.lower() in content for p in patterns):
            clean.append(m)
    return clean


# ── LLM Sync Prompt ──────────────────────────────────────────

def build_sync_prompt(store_a: list[dict], store_b: list[dict],
                      name_a: str, name_b: str) -> str:
    """Build the prompt that asks the LLM to reconcile two memory stores."""

    def format_store(memories: list[dict]) -> str:
        lines = []
        for i, m in enumerate(memories):
            content = m.get("content", str(m))
            meta_parts = []
            if "type" in m:
                meta_parts.append(f"type={m['type']}")
            if "updated" in m:
                meta_parts.append(f"updated={m['updated']}")
            elif "created" in m:
                meta_parts.append(f"created={m['created']}")
            meta = f" ({', '.join(meta_parts)})" if meta_parts else ""
            lines.append(f"  [{i+1}] {content}{meta}")
        return "\n".join(lines)

    return f"""You are a memory reconciliation engine. Two AI agents have separate memory stores about the same user. Your job is to compare them and produce a structured sync plan.

STORE A ({name_a}) — {len(store_a)} memories:
{format_store(store_a)}

STORE B ({name_b}) — {len(store_b)} memories:
{format_store(store_b)}

INSTRUCTIONS:
Compare every memory in both stores. For each, determine one of these actions:

1. DUPLICATE — Both stores have the same fact in different words. Output a merged version.
2. NEW_FOR_A — Memory exists only in B. Should be added to A.
3. NEW_FOR_B — Memory exists only in A. Should be added to B.
4. CONFLICT — Stores contradict each other. Flag with both versions and which is newer.
5. KEEP — Memory exists in one store and is not relevant to the other. No action needed.

OUTPUT FORMAT — respond with ONLY a JSON array, no other text:
[
  {{
    "action": "DUPLICATE",
    "store_a_index": 1,
    "store_b_index": 3,
    "merged": "The combined, better-worded version of both memories",
    "reasoning": "Brief explanation of why these are the same fact"
  }},
  {{
    "action": "NEW_FOR_A",
    "store_b_index": 5,
    "content": "The memory to add to Store A",
    "reasoning": "This fact from B has no equivalent in A"
  }},
  {{
    "action": "NEW_FOR_B",
    "store_a_index": 2,
    "content": "The memory to add to Store B",
    "reasoning": "This fact from A has no equivalent in B"
  }},
  {{
    "action": "CONFLICT",
    "store_a_index": 4,
    "store_b_index": 7,
    "version_a": "What A says",
    "version_b": "What B says",
    "proposed_resolution": "Which version to keep and why",
    "reasoning": "Explanation of the conflict"
  }}
]

RULES:
- Every memory in both stores must be accounted for.
- When merging duplicates, keep the most specific/detailed version. Combine if both add value.
- For conflicts, prefer the more recently updated memory if timestamps are available.
- Do NOT invent information. Only work with what's in the stores.
- If a memory is agent-specific (e.g., "I am a coding agent") and not about the user, mark as KEEP.

Respond with ONLY the JSON array. No markdown fences. No explanation outside the JSON."""


# ── LLM Call ──────────────────────────────────────────────────

def call_llm(prompt: str, model: str) -> str:
    """Send prompt to Ollama, return response text."""
    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.1, "num_predict": 8192}
        )
        return response["message"]["content"]
    except Exception as e:
        print(f"\n  Error calling Ollama: {e}")
        print(f"  Make sure Ollama is running and model '{model}' is pulled.")
        print(f"  Try: ollama pull {model}")
        sys.exit(1)


def parse_sync_response(response: str) -> list[dict]:
    """Extract the JSON array from the LLM response."""
    # Strip markdown fences if present
    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    # Find the JSON array
    start = text.find("[")
    end = text.rfind("]") + 1
    if start == -1 or end == 0:
        print("\n  Error: LLM did not return valid JSON.")
        print("  Raw response:")
        print(text[:500])
        return []

    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError as e:
        print(f"\n  Error parsing JSON: {e}")
        print("  Raw response:")
        print(text[start:end][:500])
        return []


# ── Display ───────────────────────────────────────────────────

def display_sync_plan(actions: list[dict], name_a: str, name_b: str,
                      store_a: list[dict], store_b: list[dict]):
    """Pretty-print the sync conversation."""

    counts = {"DUPLICATE": 0, "NEW_FOR_A": 0, "NEW_FOR_B": 0, "CONFLICT": 0, "KEEP": 0}

    for act in actions:
        action = act.get("action", "UNKNOWN")
        counts[action] = counts.get(action, 0) + 1

        if action == "DUPLICATE":
            idx_a = act.get("store_a_index", "?")
            idx_b = act.get("store_b_index", "?")
            a_content = _get_content(store_a, idx_a)
            b_content = _get_content(store_b, idx_b)
            print(f"\n  [{name_a}] \"{a_content}\"")
            print(f"  [{name_b}] \"{b_content}\"")
            print(f"  \033[32m[→ MERGE]\033[0m {act.get('merged', '?')}")

        elif action == "NEW_FOR_A":
            idx_b = act.get("store_b_index", "?")
            b_content = _get_content(store_b, idx_b)
            print(f"\n  [{name_b}] \"{b_content}\"")
            print(f"  [{name_a}] No equivalent.")
            print(f"  \033[36m[→ NEW for {name_a}]\033[0m {act.get('content', b_content)}")

        elif action == "NEW_FOR_B":
            idx_a = act.get("store_a_index", "?")
            a_content = _get_content(store_a, idx_a)
            print(f"\n  [{name_a}] \"{a_content}\"")
            print(f"  [{name_b}] No equivalent.")
            print(f"  \033[36m[→ NEW for {name_b}]\033[0m {act.get('content', a_content)}")

        elif action == "CONFLICT":
            print(f"\n  \033[31m[⚡ CONFLICT]\033[0m")
            print(f"  [{name_a}] \"{act.get('version_a', '?')}\"")
            print(f"  [{name_b}] \"{act.get('version_b', '?')}\"")
            print(f"  Proposed: {act.get('proposed_resolution', '?')}")

    # Summary
    print("\n" + "═" * 50)
    total_changes = counts["DUPLICATE"] + counts["NEW_FOR_A"] + counts["NEW_FOR_B"]
    print(f"  {counts['DUPLICATE']} merged  ·  "
          f"{counts['NEW_FOR_A']} new for {name_a}  ·  "
          f"{counts['NEW_FOR_B']} new for {name_b}  ·  "
          f"{counts['CONFLICT']} conflicts")
    print("═" * 50)


def _get_content(store: list[dict], index) -> str:
    """Safely get memory content by 1-indexed position."""
    try:
        idx = int(index) - 1
        if 0 <= idx < len(store):
            return store[idx].get("content", str(store[idx]))
    except (ValueError, TypeError):
        pass
    return f"[index {index}]"


# ── Apply Changes ─────────────────────────────────────────────

def apply_sync(actions: list[dict], store_a: list[dict], store_b: list[dict],
               config: dict) -> tuple[list[dict], list[dict]]:
    """Apply sync actions to produce updated stores."""

    updated_a = list(store_a)
    updated_b = list(store_b)
    now = datetime.now(timezone.utc).isoformat()

    for act in actions:
        action = act.get("action", "")

        if action == "DUPLICATE":
            # Replace both entries with merged version
            merged_memory = {
                "content": act["merged"],
                "type": "fact",
                "source": "parley_sync",
                "updated": now,
            }
            idx_a = int(act.get("store_a_index", 0)) - 1
            idx_b = int(act.get("store_b_index", 0)) - 1

            if 0 <= idx_a < len(updated_a):
                # Preserve original type if present
                merged_memory["type"] = updated_a[idx_a].get("type", "fact")
                merged_memory["created"] = updated_a[idx_a].get("created", now)
                updated_a[idx_a] = {**updated_a[idx_a], **merged_memory}
            if 0 <= idx_b < len(updated_b):
                merged_b = {**merged_memory}
                merged_b["created"] = updated_b[idx_b].get("created", now)
                updated_b[idx_b] = {**updated_b[idx_b], **merged_b}

        elif action == "NEW_FOR_A" and config.get("auto_accept_new", True):
            new_memory = {
                "content": act.get("content", ""),
                "type": "fact",
                "source": "parley_sync",
                "created": now,
                "updated": now,
            }
            updated_a.append(new_memory)

        elif action == "NEW_FOR_B" and config.get("auto_accept_new", True):
            new_memory = {
                "content": act.get("content", ""),
                "type": "fact",
                "source": "parley_sync",
                "created": now,
                "updated": now,
            }
            updated_b.append(new_memory)

        elif action == "CONFLICT":
            if not config.get("require_review_conflicts", True):
                # Auto-resolve: prefer the proposed resolution
                resolution = act.get("proposed_resolution", "")
                if "Store A" in resolution or "A" in resolution.split()[0:3]:
                    content = act.get("version_a", "")
                else:
                    content = act.get("version_b", "")
                resolved = {
                    "content": content,
                    "type": "correction",
                    "source": "parley_sync",
                    "updated": now,
                }
                idx_a = int(act.get("store_a_index", 0)) - 1
                idx_b = int(act.get("store_b_index", 0)) - 1
                if 0 <= idx_a < len(updated_a):
                    updated_a[idx_a] = {**updated_a[idx_a], **resolved}
                if 0 <= idx_b < len(updated_b):
                    updated_b[idx_b] = {**updated_b[idx_b], **resolved}

    return updated_a, updated_b


# ── Logging ───────────────────────────────────────────────────

def save_log(actions: list[dict], name_a: str, name_b: str,
             store_a: list[dict], store_b: list[dict], config: dict):
    """Save the sync conversation to a log file."""
    if not config.get("save_conversations", True):
        return

    log_dir = Path("parley_logs")
    log_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    ext = "md" if config.get("log_format") == "markdown" else "json"
    log_path = log_dir / f"sync_{timestamp}.{ext}"

    if ext == "json":
        with open(log_path, "w") as f:
            json.dump({
                "timestamp": timestamp,
                "store_a": name_a,
                "store_b": name_b,
                "actions": actions,
            }, f, indent=2)
    else:
        with open(log_path, "w") as f:
            f.write(f"# Parley Sync — {timestamp}\n\n")
            f.write(f"**Store A:** {name_a} ({len(store_a)} memories)\n")
            f.write(f"**Store B:** {name_b} ({len(store_b)} memories)\n\n")
            for act in actions:
                action = act.get("action", "?")
                f.write(f"### {action}\n")
                f.write(f"{act.get('reasoning', '')}\n\n")

    print(f"\n  Log saved: {log_path}")


# ── Main ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Parley — Sync agent memories through conversation."
    )
    parser.add_argument("--store-a", required=True, help="Path to first memory store")
    parser.add_argument("--store-b", required=True, help="Path to second memory store")
    parser.add_argument("--adapter-a", help="Custom adapter class for store A (module.Class)")
    parser.add_argument("--adapter-b", help="Custom adapter class for store B (module.Class)")
    parser.add_argument("--model", help="Ollama model to use (default: from config or llama3.1:8b)")
    parser.add_argument("--review", action="store_true", help="Review changes before applying")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without writing changes")
    parser.add_argument("--name-a", help="Display name for store A")
    parser.add_argument("--name-b", help="Display name for store B")

    args = parser.parse_args()
    config = load_config()

    if args.model:
        config["model"] = args.model

    name_a = args.name_a or Path(args.store_a).stem
    name_b = args.name_b or Path(args.store_b).stem

    # ── Load stores ───────────────────────────────────────────
    adapter_a = get_adapter(args.store_a, args.adapter_a)
    adapter_b = get_adapter(args.store_b, args.adapter_b)

    store_a = adapter_a.read(args.store_a)
    store_b = adapter_b.read(args.store_b)

    # ── Redact sensitive memories ─────────────────────────────
    redact = config.get("redact_patterns", [])
    store_a_clean = redact_memories(store_a, redact)
    store_b_clean = redact_memories(store_b, redact)

    # ── Banner ────────────────────────────────────────────────
    print(BANNER)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"  {now}")
    print(f"  Store A: {args.store_a} ({len(store_a)} memories, {len(store_a) - len(store_a_clean)} redacted)")
    print(f"  Store B: {args.store_b} ({len(store_b)} memories, {len(store_b) - len(store_b_clean)} redacted)")
    print(f"  Model: {config['model']}")
    print("═" * 50)

    # ── Build prompt and call LLM ─────────────────────────────
    print("\n  Analyzing memories...")
    prompt = build_sync_prompt(store_a_clean, store_b_clean, name_a, name_b)
    response = call_llm(prompt, config["model"])

    # ── Parse response ────────────────────────────────────────
    actions = parse_sync_response(response)
    if not actions:
        print("\n  No sync actions produced. Stores may already be in sync.")
        return

    # ── Display ───────────────────────────────────────────────
    display_sync_plan(actions, name_a, name_b, store_a_clean, store_b_clean)

    # ── Save log ──────────────────────────────────────────────
    save_log(actions, name_a, name_b, store_a_clean, store_b_clean, config)

    # ── Dry run exit ──────────────────────────────────────────
    if args.dry_run:
        print("\n  Dry run — no changes written.")
        return

    # ── Review gate ───────────────────────────────────────────
    if args.review:
        response = input("\n  Apply these changes? [y/N] ").strip().lower()
        if response != "y":
            print("  Aborted. No changes written.")
            return

    # ── Apply ─────────────────────────────────────────────────
    updated_a, updated_b = apply_sync(actions, store_a, store_b, config)
    adapter_a.write(args.store_a, updated_a)
    adapter_b.write(args.store_b, updated_b)

    print(f"\n  ✓ Store A updated: {args.store_a}")
    print(f"  ✓ Store B updated: {args.store_b}")
    print(f"  Done.\n")


if __name__ == "__main__":
    main()
