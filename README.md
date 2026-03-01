# Clade

**Sync AI agent memories through conversation.**

A clade is a group sharing a common ancestor. Your agents share you.

---

## Why Clade Exists

### The LLM is the universal adapter

The software industry's answer to agent interop: build protocols. A2A, MCP, custom SDKs. All require every agent to implement the same spec.

Clade's answer: every agent already speaks the same language — natural language.

Point Clade at any two files. JSON, Markdown, YAML, plaintext, CSV, a database dump. The LLM reads both, figures out the format, extracts the memories, and reconciles them.

No adapter code. No format negotiation. No SDK. The protocol is the conversation. The conversation is the protocol.

### Your memories never leave your machine

Every AI company stores your memories on their servers. OpenAI, Anthropic, Google — they remember you because their architecture requires it. Your preferences, your decisions, your context — stored in someone else's database.

Clade runs on a local LLM. Ollama on your hardware. Your memories never touch a network. There is no server. There is no account. The conversation between your agents happens in a room nobody else can enter, because the room is your computer.

This is not a feature. It is a design principle.
---

## How It Works

```
┌─────────────┐    ┌─────────────┐
│  Agent A     │    │  Agent B     │
│  Memory      │    │  Memory      │
│ (any format) │    │ (any format) │
└──────┬───────┘    └──────┬───────┘
       │                   │
       ▼                   ▼
  ┌────────────────────────────┐
  │        Local LLM           │
  │   (Ollama / your machine)  │
  │                            │
  │   1. Reads both files      │
  │   2. Figures out formats   │
  │   3. Extracts memories     │
  │   4. Finds duplicates      │
  │   5. Flags conflicts       │
  │   6. Proposes merges       │
  │   7. You review & approve  │
  ├────────────────────────────┤
  │  Nothing leaves your       │
  │  machine.                  │
  └────────────────────────────┘
```

## Quick Start

```bash
pip install -r requirements.txt
ollama pull llama3.1:8b

# Sync two agent memory stores (any format)
python clade.py --store-a memories_a.json --store-b memories_b.md --review

# Dry run (see the plan without changing anything)
python clade.py --store-a memories_a.json --store-b memories_b.md --dry-run

# Use a larger model for complex stores
python clade.py --store-a big_store.json --store-b other_store.yaml --model llama3.1:70b --review
```

## Try the Examples

```bash
# JSON vs JSON
python clade.py --store-a examples/scope_agent.json --store-b examples/openclaw_agent.json --dry-run

# JSON vs Markdown
python clade.py --store-a examples/scope_agent.json --store-b examples/markdown_agent.md --dry-run

# Markdown vs Plaintext
python clade.py --store-a examples/markdown_agent.md --store-b examples/plaintext_agent.txt --dry-run

# Plaintext vs YAML
python clade.py --store-a examples/plaintext_agent.txt --store-b examples/yaml_agent.yaml --dry-run
```

Four formats. Zero adapters. One LLM.

## What a Sync Looks Like

Agent A stores memories as JSON. Agent B uses Markdown. Clade doesn't care.

```
[Agent A — JSON] "user_preference": "dark interfaces with warm tones"
[Agent B — Markdown] "## UI: User wants dark mode, background #2b2a27"
→ MERGE: "User prefers dark interfaces with warm tones. Specific: #2b2a27 background."

[Agent A — JSON] "location": "Frankfurt" (updated Feb 28)
[Agent B — Markdown] "Lives in Berlin" (noted Jan 15)
→ CONFLICT: Agent A says Frankfurt (newer). Agent B says Berlin (older). Flagged for review.

[Agent A only] "Working on app called Scope, local-first architecture"
→ NEW FOR B: Propagated to Agent B's store.
```

## What You Can Sync

Clade reads any text-based format. Tested with:

- JSON memory stores (Claude, custom agents)
- Markdown files (notes, knowledge bases)
- Plain text logs
- YAML configurations
- CSV exports
- SQLite dumps (via `.dump`)

If a human can read the file, the LLM can read it. That's the point.

## Why No Adapters?

Our first version had adapters — JSONAdapter, TextAdapter, a base class, a plugin system. Then we realized: adapters contradict our own thesis.

If the core idea is that natural language is the universal integration layer, then why are we writing format-specific parsers?

The LLM reads JSON. It reads Markdown. It reads YAML. It reads plaintext. It figures out the structure on its own. Adapter code only existed because machines couldn't read unstructured text. LLMs removed that constraint. We're the first ones to take it seriously for agent memory.

## Roadmap

Done:
- [x] Local LLM sync via Ollama
- [x] Format-agnostic — reads any text-based file
- [x] Conflict detection with timestamp resolution
- [x] Review mode with human approval
- [x] Dry run mode
- [x] Conversation logging (Markdown + JSON)

Next:
- [ ] Stress test against real-world memory formats (Letta, LangChain, MemGPT, CrewAI)
- [ ] Handle binary formats (SQLite → automatic dump → sync)
- [ ] Multi-file agent stores (memory spread across directories)
- [ ] Scheduled sync (cron/launchd — set it and forget it)
- [ ] Semantic similarity pre-filtering (local embeddings for large stores)
- [ ] Multi-store sync (3+ agents in one session)
- [ ] Web UI for reviewing sync conversations
- [ ] Embeddable engine for app integration

## Contributing

We don't need adapter code. The LLM is the adapter.

What we need:

**Test with your actual agent memories.** Point Clade at the real files your agents produce. Tell us what breaks. That's the most valuable contribution.

**Share formats we haven't seen.** If your agent stores memories in a format not listed above, open an issue with an anonymized sample. We'll test it.

**Edge cases.** What happens with 500+ memories? Conflicting timestamps across time zones? Memories in multiple languages? Mixed formats in one file? Find the limits.

**Integrations.** Want Clade built into your app or framework? Open a discussion. The engine is ~150 lines and MIT licensed.

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## The Name

A clade is a biological term for a group sharing a common ancestor.

Your AI agents share a common ancestor — you. They inherited fragments of your knowledge, diverged through separate conversations, adapted to different niches in your workflow.

Clade brings them back together. Through conversation. On your machine. Answering to nobody.

---

*"The best integration protocol is the one you don't have to implement."*
