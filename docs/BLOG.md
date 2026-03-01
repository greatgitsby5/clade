# Your AI Agents Don't Talk to Each Other. Here's a Fix That Doesn't Need a Protocol.

You use multiple AI agents. Maybe Claude for thinking, ChatGPT for research, a coding agent for building, a custom bot on Discord. Each one learns things about you. None of them share what they know.

The industry is building protocols to fix this. Google released A2A. Anthropic has MCP. Cisco is proposing an "Internet of Cognition." All of them require every agent to implement the same spec, speak the same technical language, agree on the same schema.

We built something simpler. It's called Parley.

## The Idea

Every AI agent already speaks the same language: natural language. A fact like "James prefers dark interfaces" doesn't need a schema to be understood. It needs to be read.

Parley takes two agent memory stores — in any format — and feeds them to a local LLM. The LLM compares every memory, identifies duplicates, finds conflicts, and proposes a merge. It outputs this as a structured conversation between the two agents. You review it. You approve it. Both stores get updated.

No network. No central server. No protocol to implement. The LLM is the protocol.

## What It Looks Like

```
[Scope Agent] "User prefers dark interfaces with warm tones"
[OpenClaw Bot] "User wants dark mode, specifically #2b2a27 background"
[→ MERGE] "User prefers dark interfaces with warm tones.
    Specific preference: #2b2a27 background."
```

```
[Scope Agent] "User moved from Berlin to Frankfurt"
[OpenClaw Bot] "User lives in Berlin"
[⚡ CONFLICT] Scope says Frankfurt (updated Feb 28).
    OpenClaw says Berlin (updated Jan 15).
    Resolution: Accept Scope's version (newer).
```

The entire sync runs locally on your machine. Your memories never touch a server.

## Why Natural Language as the Integration Layer?

Every agent framework stores memories differently. Letta uses structured notes with embeddings. LangChain uses key-value stores. Some agents just dump facts into text files. The conventional wisdom says you need a universal format — a standard everyone agrees on.

But getting everyone to agree on a standard is how you end up with fifteen competing standards. (Relevant XKCD: 927.)

Natural language sidesteps the problem. If a memory is expressible in words — and all memories are — then any LLM can read it, compare it, and merge it. The "schema" is English (or German, or Japanese). The "API" is a prompt. The "integration" is reading a file.

This is either too obvious or too simple. We think it's both, and that's why nobody's built it yet.

## Why Local?

Your agent memories are the most personal data you have. Where you live. What you're building. What decisions you've made. What you've changed your mind about.

The idea that you should upload this to a cloud service to sync it between your own agents is absurd. Parley runs on Ollama. Everything stays on your hardware. This isn't a feature you can turn off — it's the architecture.

## What's Next

Parley is a 200-line Python script with a big idea behind it. Right now it syncs JSON files. We're building:

- Adapters for popular agent frameworks (LangChain, Letta, OpenClaw, AutoGen)
- Scheduled sync via cron
- Semantic similarity matching with local embeddings
- Multi-store sync (3+ agents in one session)

But the most important thing is testing with real memories from real agent setups. If you run multiple AI agents, try syncing them with Parley and tell us what breaks.

## Get It

GitHub: [github.com/yourusername/parley](https://github.com/yourusername/parley)

MIT licensed. One dependency (Ollama). Works today.

---

*Parley was built during the development of Scope, a local-first AI companion. The sync concept emerged from a simple question: if I have two agents that both know things about me, why can't they just... talk?*
