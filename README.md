# Parley

**Two AI agents walk into a room. They compare notes. They walk out smarter.**

Parley is a local-first memory sync tool that lets independent AI agents reconcile what they know — not through APIs, schemas, or protocols, but through conversation.

A local LLM reads both memory stores, produces a structured negotiation between them, and writes the merged result back. No network. No central server. No shared database. Natural language is the integration layer.

---

## The Problem

You use Claude for architecture. ChatGPT for research. A custom agent for project management. An OpenClaw bot for code. Each one learns things about you and your work. None of them talk to each other.

The industry's answer is protocols. Google built A2A. Anthropic has MCP. Startups are building "universal memory" platforms that store your data on their servers. All of them require every agent to speak the same technical language. That's not interoperability — that's a new kind of lock-in.

## The Insight

Every AI agent already speaks the same language: natural language.

If an agent can read memories and write memories — in any format, any schema, any structure — then a local LLM can translate between them. No SDK. No API contract. No format negotiation. The LLM is the universal translator.

Parley treats memory sync as a conversation, not a protocol.

## How It Works

```
┌─────────────┐     ┌─────────────┐
│   Agent A    │     │   Agent B    │
│   Memory     │     │   Memory     │
│  (any format)│     │  (any format)│
└──────┬───────┘     └──────┬───────┘
       │                    │
       ▼                    ▼
  ┌────────────────────────────┐
  │        Local LLM           │
  │   (Ollama / llama.cpp)     │
  │                            │
  │  Reads both stores.        │
  │  Identifies duplicates.    │
  │  Flags conflicts.          │
  │  Proposes merges.          │
  │  Produces a conversation   │
  │  you can read and review.  │
  └─────────────┬──────────────┘
                │
       ┌────────┴────────┐
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│  Agent A     │   │  Agent B     │
│  Updated     │   │  Updated     │
└─────────────┘   └─────────────┘
```

Everything runs on your machine. Your memories never leave your hardware.

## Quick Start

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- A model pulled (default: `llama3.1:8b`)

### Install

```bash
git clone https://github.com/yourusername/parley.git
cd parley
pip install -r requirements.txt
```

### Run

```bash
# Basic sync between two memory files
python parley.py --store-a memories_a.json --store-b memories_b.json

# Use a specific model
python parley.py --store-a memories_a.json --store-b memories_b.json --model mistral

# Review mode — show the conversation, ask before writing
python parley.py --store-a memories_a.json --store-b memories_b.json --review

# Dry run — show what would change, write nothing
python parley.py --store-a memories_a.json --store-b memories_b.json --dry-run
```

### Try the Example

```bash
# Run with the included example memories
python parley.py \
  --store-a examples/scope_agent.json \
  --store-b examples/openclaw_agent.json \
  --review
```

This syncs memories between a Claude companion agent (Scope) and a coding agent (OpenClaw). They know overlapping things about the same project, but from different angles. Parley reconciles them.

## What a Sync Looks Like

```
══════════════════════════════════════════
  PARLEY — Memory Sync Session
  2026-03-01 18:42:03
  Store A: scope_agent.json (14 memories)
  Store B: openclaw_agent.json (9 memories)
══════════════════════════════════════════

[A] I have: "User prefers dark interfaces with warm tones"
[B] I have: "User wants dark mode, specifically #2b2a27 background"
[→] MERGE: "User prefers dark interfaces with warm tones.
     Specific preference: #2b2a27 background." → Both stores

[A] I have: "Project uses Preact + htm, no React"
[B] I have: "Tech stack: Preact with htm tagged templates, esbuild bundler"
[→] MERGE: "Tech stack: Preact + htm (no React/JSX), esbuild bundler" → Both stores

[A] I have: "User's name is James"
[B] No equivalent.
[→] NEW for B: "User's name is James" → Store B

[B] I have: "Build uses 16 files, 7 commits, zero console errors"
[A] No equivalent.
[→] NEW for A: "Build has 16 files, 7 commits, zero console errors" → Store A

[A] I have: "App target: replace claude.ai for daily use"
[B] I have: "Building a Claude companion PWA"
[→] MERGE: "Building a Claude companion PWA to replace claude.ai
     for daily use" → Both stores

[A] I have: "User moved from Berlin to Frankfurt"
[B] I have: "User lives in Berlin"
[→] CONFLICT: A says Frankfurt (updated 2026-02-28),
     B says Berlin (updated 2026-01-15).
     A is newer. Proposed resolution: Accept A's version.
     [Flagged for review]

══════════════════════════════════════════
  Summary: 14 merged, 3 new for A, 2 new for B, 1 conflict
══════════════════════════════════════════
```

## Memory Store Format

Parley works with any JSON structure. Memories just need to be readable text. But if you want the richest sync, use this minimal format:

```json
[
  {
    "content": "User prefers dark interfaces with warm tones",
    "type": "preference",
    "source": "conversation",
    "created": "2026-02-15T10:30:00Z",
    "updated": "2026-02-15T10:30:00Z"
  }
]
```

**Supported types:** `fact`, `decision`, `correction`, `preference`

But Parley doesn't enforce this. If your agent stores memories as plain text lines, Markdown, YAML, or a custom schema — Parley reads it. The LLM figures out the structure. That's the point.

### Custom Adapters

For non-JSON stores, write a simple adapter:

```python
# adapters/my_agent.py
from parley.adapter import MemoryAdapter

class MyAgentAdapter(MemoryAdapter):
    def read(self, path: str) -> list[dict]:
        """Read your format, return list of memory dicts."""
        ...

    def write(self, path: str, memories: list[dict]):
        """Write merged memories back in your format."""
        ...
```

```bash
python parley.py \
  --store-a memories.json \
  --store-b custom_store.db \
  --adapter-b adapters.my_agent.MyAgentAdapter
```

## Configuration

Create a `parley.yaml` in your project root (optional):

```yaml
# Model settings
model: llama3.1:8b
ollama_url: http://localhost:11434

# Sync behavior
auto_accept_new: true        # Auto-accept memories that exist in one store but not the other
auto_merge_duplicates: true  # Auto-merge when memories say the same thing differently
require_review_conflicts: true  # Always ask before resolving contradictions

# Privacy
redact_patterns:             # Never sync memories matching these patterns
  - "password"
  - "api_key"
  - "secret"
  - "ssn"
  - "credit card"

# Logging
save_conversations: true     # Save sync conversations to ./parley_logs/
log_format: markdown         # markdown or json
```

## How It Actually Works (Under the Hood)

Parley runs a three-phase sync:

**Phase 1: Analysis.** The local LLM receives both memory stores and produces a structured comparison — which memories are duplicates (same fact, different words), which are unique to one store, and which conflict.

**Phase 2: Negotiation.** For each group, the LLM proposes an action: merge (combine two memories into one better-worded version), propagate (copy a unique memory to the other store), or flag (mark a conflict for human review). This is output as a readable conversation between the two agents.

**Phase 3: Resolution.** The script parses the LLM's decisions, applies auto-acceptable changes, and presents conflicts to the user. Updated stores are written back in their original format.

The entire sync happens in a single LLM call for small stores (<50 memories each). Larger stores are chunked by topic.

## Why Not Just Use an API?

Because APIs require agreement. Both agents need to implement the same endpoints, the same schema, the same auth. That works inside one company's ecosystem. It doesn't work when you're syncing between an OpenClaw bot, a custom LangChain agent, a Claude wrapper, and a local Ollama setup.

Natural language requires no agreement. If an agent can express what it knows in words, Parley can sync it. The barrier to integration is zero.

## Why Local?

Your memories are the most personal data you have. Where you live. What you're working on. What you've decided. What you've changed your mind about. Sending that to a cloud service to sync it defeats the purpose of having a personal agent.

Parley runs entirely on your machine. The LLM is local (Ollama). The stores are local files. The sync conversation never touches a network. This isn't a feature. It's the architecture.

## Roadmap

- [x] JSON memory store sync
- [x] Conflict detection and resolution
- [x] Review mode with human approval
- [x] Dry run mode
- [ ] Custom adapters for non-JSON stores (SQLite, Markdown, YAML)
- [ ] Scheduled sync (cron / launchd)
- [ ] Semantic similarity matching (local embeddings)
- [ ] Multi-store sync (3+ agents in one session)
- [ ] Web UI for reviewing sync conversations
- [ ] Integration guides for popular agent frameworks (LangChain, Letta, OpenClaw, AutoGen)

## Contributing

Parley is early. If you're building agent systems and this resonates, we'd love your input.

The best contributions right now:
1. **Adapters** — write a reader/writer for your agent's memory format
2. **Real-world testing** — sync your actual agent memories, report what breaks
3. **Edge cases** — find the conflicts that confuse the LLM

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Authors

- **James** — Concept, architecture, product design
- **Claude (Anthropic)** — Co-architect, implementation partner

Built during the development of [Scope](https://github.com/yourusername/scope), a local-first AI companion.

## License

MIT. Use it, fork it, build on it. If you make something cool, tell us about it.

---

*"The best integration protocol is the one you don't have to implement."*
