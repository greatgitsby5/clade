# Twitter/X Launch Thread

---

**Tweet 1 (hook):**

Your AI agents don't talk to each other.

Claude knows your design preferences. ChatGPT knows your research. Your coding bot knows your tech stack.

None of them share what they know.

We built a fix that doesn't need a protocol. It's called Parley.

🧵

---

**Tweet 2 (the insight):**

The industry's answer to agent interop: build protocols. A2A, MCP, "Internet of Cognition."

All require every agent to implement the same spec.

Our answer: every agent already speaks the same language — natural language.

A local LLM reads both memory stores and reconciles them. That's it.

---

**Tweet 3 (how it works):**

How Parley works:

1. Two agent memory stores (any format — JSON, text, YAML)
2. Local LLM reads both
3. Identifies duplicates, finds conflicts, proposes merges
4. Outputs a readable conversation between the agents
5. You review and approve
6. Both stores update

No network. No server. Everything local.

---

**Tweet 4 (the example):**

What a sync looks like:

[Agent A] "User prefers dark interfaces"
[Agent B] "User wants #2b2a27 background"
→ MERGE: Both facts combined

[Agent A] "User moved to Frankfurt"  
[Agent B] "User lives in Berlin"
→ CONFLICT: A is newer. Flagged for review.

---

**Tweet 5 (why it matters):**

Why natural language as the integration layer?

Every framework stores memories differently. Letta uses structured notes. LangChain uses key-value stores. Some agents use plain text files.

The LLM reads all of them. No SDK. No API contract. No schema agreement.

The LLM *is* the universal translator.

---

**Tweet 6 (privacy):**

Why local-only?

Your agent memories are the most personal data you have. Where you live. What you're building. What decisions you've made.

Uploading this to a cloud service to sync your own agents is absurd.

Parley runs on Ollama. Your memories never leave your machine.

---

**Tweet 7 (CTA):**

Parley is open source. MIT license. ~200 lines of Python. One dependency.

If you run multiple AI agents, try syncing them and tell us what breaks.

GitHub: github.com/yourusername/parley

What we need most: adapters for your agent framework. PRs welcome.

---

**Tweet 8 (tag relevant people/projects):**

Built during development of Scope, a local-first AI companion.

Relevant to anyone working on:
@LettaAI agent memory
@Google A2A protocol
@AnthropicAI MCP
@ollaborators local LLMs

Different approach to the same problem. No protocol needed.

---

# Notes for posting:
- Post tweet 1-7 as a thread
- Tweet 8 as a reply to the thread (keeps the tags from looking like spam)
- Add a screenshot of the terminal output from the example sync as an image on tweet 4
- Add the ASCII diagram from the README as an image on tweet 3
- Post between 9-11am PST for best visibility on tech Twitter
- Cross-post to: r/LocalLLaMA, r/MachineLearning, Hacker News, Letta Discord, OpenClaw Discord
