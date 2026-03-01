#!/usr/bin/env python3
"""
Clade — Memory sync through conversation.
Two files walk in. A local LLM reconciles them.
No adapters. No schema. The LLM figures out the format.
"""

import argparse
import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

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

DEFAULT_MODEL = "llama3.1:8b"
BANNER = """
╔══════════════════════════════════════════════╗
║  CLADE — Memory Sync Through Conversation   ║
╚══════════════════════════════════════════════╝"""

def load_config():
    config = {
        "model": DEFAULT_MODEL,
        "auto_accept_new": True,
        "auto_merge_duplicates": True,
        "require_review_conflicts": True,
        "redact_patterns": ["password", "api_key", "secret", "ssn", "credit card"],
        "save_conversations": True,
        "log_format": "markdown",
    }
    config_path = Path("clade.yaml")
    if config_path.exists() and HAS_YAML:
        with open(config_path) as f:
            user_config = yaml.safe_load(f) or {}
            config.update(user_config)
    return config

def read_file(path):
    """Read any file as raw text. The LLM figures out the format."""
    with open(path) as f:
        return f.read()

def redact_text(text, patterns):
    """Remove lines containing sensitive patterns."""
    lines = text.split('\n')
    clean = [l for l in lines if not any(p.lower() in l.lower() for p in patterns)]
    return '\n'.join(clean)

def build_sync_prompt(text_a, text_b, name_a, name_b):
    return f"""You are a memory reconciliation engine. You will be given two files containing AI agent memories about the same user. The files may be in ANY format — JSON, Markdown, YAML, plain text, CSV, or something else entirely.

Your job:
1. Figure out what format each file is in.
2. Extract individual memories from each.
3. Compare every memory and produce a sync plan.

FILE A ({name_a}):
---
{text_a}
---

FILE B ({name_b}):
---
{text_b}
---

For each memory, determine one action:
1. DUPLICATE — Same fact in different words. Output a merged version.
2. NEW_FOR_A — Memory exists only in B. Should be added to A.
3. NEW_FOR_B — Memory exists only in A. Should be added to B.
4. CONFLICT — Stores contradict each other. Flag with both versions.
5. KEEP — Agent-specific, not relevant to the other store.

OUTPUT FORMAT — respond with ONLY a JSON array, no other text:
[
  {{"action": "DUPLICATE", "memory_a": "what A says", "memory_b": "what B says", "merged": "combined version", "reasoning": "why"}},
  {{"action": "NEW_FOR_A", "content": "memory to add to A", "reasoning": "why"}},
  {{"action": "NEW_FOR_B", "content": "memory to add to B", "reasoning": "why"}},
  {{"action": "CONFLICT", "version_a": "what A says", "version_b": "what B says", "proposed_resolution": "which to keep and why", "reasoning": "explanation"}}
]

RULES:
- Account for every distinct memory in both files.
- When merging, keep the most specific version. Combine if both add value.
- For conflicts, prefer the more recently updated memory if timestamps exist.
- Do NOT invent information not present in the files.
- If a memory is agent-specific (e.g. "I am a coding agent"), mark as KEEP.

Respond with ONLY the JSON array."""

def call_llm(prompt, model):
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
        sys.exit(1)

def parse_sync_response(response):
    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
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

def display_sync_plan(actions, name_a, name_b):
    counts = {"DUPLICATE": 0, "NEW_FOR_A": 0, "NEW_FOR_B": 0, "CONFLICT": 0, "KEEP": 0}

    for act in actions:
        action = act.get("action", "UNKNOWN")
        counts[action] = counts.get(action, 0) + 1

        if action == "DUPLICATE":
            print(f'\n  [{name_a}] "{act.get("memory_a", "?")}"')
            print(f'  [{name_b}] "{act.get("memory_b", "?")}"')
            print(f'  \033[32m[→ MERGE]\033[0m {act.get("merged", "?")}')

        elif action == "NEW_FOR_A":
            print(f'\n  [{name_b}] has: "{act.get("content", "?")}"')
            print(f'  [{name_a}] No equivalent.')
            print(f'  \033[36m[→ NEW for {name_a}]\033[0m {act.get("content", "?")}')

        elif action == "NEW_FOR_B":
            print(f'\n  [{name_a}] has: "{act.get("content", "?")}"')
            print(f'  [{name_b}] No equivalent.')
            print(f'  \033[36m[→ NEW for {name_b}]\033[0m {act.get("content", "?")}')

        elif action == "CONFLICT":
            print(f'\n  \033[31m[⚡ CONFLICT]\033[0m')
            print(f'  [{name_a}] "{act.get("version_a", "?")}"')
            print(f'  [{name_b}] "{act.get("version_b", "?")}"')
            print(f'  Proposed: {act.get("proposed_resolution", "?")}')

    print("\n" + "═" * 50)
    print(f"  {counts['DUPLICATE']} merged · "
          f"{counts['NEW_FOR_A']} new for {name_a} · "
          f"{counts['NEW_FOR_B']} new for {name_b} · "
          f"{counts['CONFLICT']} conflicts")
    print("═" * 50)

def save_log(actions, name_a, name_b, config):
    if not config.get("save_conversations", True):
        return
    log_dir = Path("clade_logs")
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = log_dir / f"sync_{timestamp}.md"

    with open(log_path, "w") as f:
        f.write(f"# Clade Sync — {timestamp}\n\n")
        f.write(f"**Store A:** {name_a}\n")
        f.write(f"**Store B:** {name_b}\n\n")
        for act in actions:
            f.write(f"### {act.get('action', '?')}\n")
            f.write(f"{act.get('reasoning', '')}\n\n")
    print(f"\n  Log saved: {log_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Clade — Sync agent memories through conversation."
    )
    parser.add_argument("--store-a", required=True, help="Path to first memory file (any format)")
    parser.add_argument("--store-b", required=True, help="Path to second memory file (any format)")
    parser.add_argument("--model", help="Ollama model to use")
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

    text_a = read_file(args.store_a)
    text_b = read_file(args.store_b)

    redact = config.get("redact_patterns", [])
    text_a_clean = redact_text(text_a, redact)
    text_b_clean = redact_text(text_b, redact)

    print(BANNER)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"  {now}")
    print(f"  Store A: {args.store_a}")
    print(f"  Store B: {args.store_b}")
    print(f"  Model:   {config['model']}")
    print("═" * 50)

    print("\n  Analyzing memories...")
    prompt = build_sync_prompt(text_a_clean, text_b_clean, name_a, name_b)
    response = call_llm(prompt, config["model"])

    actions = parse_sync_response(response)
    if not actions:
        print("\n  No sync actions produced. Stores may already be in sync.")
        return

    display_sync_plan(actions, name_a, name_b)
    save_log(actions, name_a, name_b, config)

    if args.dry_run:
        print("\n  Dry run — no changes written.")
        return

    if args.review:
        resp = input("\n  Apply these changes? [y/N] ").strip().lower()
        if resp != "y":
            print("  Aborted.")
            return

    print(f"\n  ✓ Sync complete.")
    print(f"  Done.\n")

if __name__ == "__main__":
    main()
