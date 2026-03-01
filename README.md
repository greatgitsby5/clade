# Clade

**A clade is a group sharing a common ancestor. Your AI agents share one: you.**

**They compare notes. They walk out smarter.**

Clade is a local-first memory sync tool that lets independent AI agents reconcile what they know — not through APIs, schemas, or protocols, but through conversation. A local LLM reads both memory files, produces a structured negotiation between them, and writes the merged result back. No network. No central server. No adapters. Natural language is the integration layer. **The LLM is the universal adapter.**

---

## The Problem

You use Claude for architecture. ChatGPT for research. A custom agent for project management. Each one learns things about you. None of them talk to each other.

The industry's answer is protocols and adapters. Google built A2A. Anthropic has MCP. All require every agent to speak the same technical language.

## The Insight

Every AI agent already speaks the same language: natural language. Point Clade at any two files — JSON, Markdown, YAML, plaintext, CSV, database dumps — and the LLM figures out the format, extracts the memories, and reconciles them.

No SDK. No API contract. No format negotiation. No adapters. **The LLM is the adapter.**

## How It Works

```
┌─────────────┐    ┌─────────────┐
│  Any file    │    │  Any file    │
│ (any format) │    │ (any format) │
└──────┬───────┘    └──────┬───────┘
       │                   │
       ▼                   ▼
  ┌────────────────────────────┐
  │        Local LLM           │
  │   (Ollama / llama.cpp)     │
  │                            │
  │   Reads both files.        │
  │   Figures out the format.  │
  │   Extracts memories.       │
  │   Identifies duplicates.   │
  │   Flags conflicts.         │
  │   Proposes merges.         │
  └─────────────┬──────────────┘
                │
       ┌────────┴────────┐
       ▼                 ▼
  ┌─────────┐      ┌─────────┐
  │ Updated │      │ Updated │
  └─────────┘      └─────────┘
```

Everything runs on your machine. Your memories never leave your hardware.

## Quick Start

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- A model pulled (default: `llama3.1:8b`)

### Install

```bash
git clone https://github.com/greatgitsby5/clade.git
cd clade
pip install -r requirements.txt
```

### Run

```bash
# Sync any two files — JSON, Markdown, plaintext, whatever
python clade.py --store-a memories_a.json --store-b memories_b.md

# Review mode — show the plan, ask before applying
python clade.py --store-a memories_a.json --store-b notes.txt --review

# Dry run — show what would change, write nothing
python clade.py --store-a agent1.json --store-b agent2.txt --dry-run
```

### Try the Examples

```bash
# JSON vs JSON
python clade.py --store-a examples/scope_agent.json --store-b examples/openclaw_agent.json --dry-run

# JSON vs Markdown
python clade.py --store-a examples/scope_agent.json --store-b examples/markdown_agent.md --dry-run

# Markdown vs Plaintext
python clade.py --store-a examples/markdown_agent.md --store-b examples/plaintext_agent.txt --dry-run
```

Three formats. Zero adapters. The LLM just reads them.

## What a Sync Looks Like

```
══════════════════════════════════════════════
  CLADE — Memory Sync Session
══════════════════════════════════════════════

  [A] "User prefers dark interfaces with warm tones"
  [B] "User wants dark mode, specifically #2b2a27 background"
  [→ MERGE] "User prefers dark interfaces with warm tones. Specific: #2b2a27 background."

  [A] "User moved from Berlin to Frankfurt"
  [B] "User lives in Berlin"
  [⚡ CONFLICT] A says Frankfurt (newer). B says Berlin.
  Proposed: Accept A's version.

══════════════════════════════════════════════
  5 merged · 3 new for A · 2 new for B · 1 conflict
══════════════════════════════════════════════
```

## Why No Adapters?

Our first version had adapters — JSONAdapter, TextAdapter, a base class, a plugin system. Then we realized: **adapters contradict our own thesis.**

If the core idea is that natural language is the universal integration layer — that an LLM can read any format — then why are we writing format-specific parsers?

The LLM reads JSON. It reads Markdown. It reads YAML. It reads plaintext. It reads CSV. It reads database dumps. It figures out the structure on its own.

The adapter pattern assumes you need to translate between formats. Clade assumes you don't. **The LLM is the translator.**

## Why Local?

Your memories are the most personal data you have. Where you live. What you're working on. What you've decided. What you've changed your mind about. Sending that to a cloud service to sync your own agents is absurd.

Clade runs entirely on your machine. The LLM is local (Ollama). The files are local. The sync never touches a network.

## Roadmap

- [x] Any-format memory file sync
- [x] Conflict detection and resolution
- [x] Review mode with human approval
- [x] Dry run mode
- [ ] Test against real-world memory formats (Letta, LangChain, MemGPT, AutoGen)
- [ ] Handle binary formats via extraction (SQLite → dump → sync)
- [ ] Multi-file agent stores (memory spread across multiple files)
- [ ] Scheduled sync (cron / launchd)
- [ ] Semantic similarity matching (local embeddings)
- [ ] Multi-store sync (3+ agents in one session)
- [ ] Web UI for reviewing sync conversations

## Contributing

The best contributions right now:

1. **Test against your agent's actual memory files** — whatever format they're in, point Clade at them and report what breaks
2. **Share memory formats we haven't seen** — so we can verify the LLM handles them
3. **Edge cases** — what happens with 500+ memories? Conflicting timestamps? Multiple languages?

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT. Use it, fork it, build on it.

---

*"The best integration protocol is the one you don't have to implement."*
