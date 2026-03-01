# Contributing to Clade

## What We Need Most

1. **Test against your agent's actual memory files** — whatever format, point Clade at them and report what breaks
2. **Share memory formats we haven't seen** — so we can verify the LLM handles them
3. **Edge cases** — 500+ memories? Conflicting timestamps? Multiple languages? Mixed formats?

## How to Test

```bash
python clade.py --store-a your_agent_memories.json --store-b another_agent.txt --dry-run
```

If the LLM gets confused by your format, open an issue with:
- The file format (anonymized if needed)
- What the LLM got wrong
- What model you used

## Pull Requests

- Keep it simple. Clade is ~150 lines for a reason.
- Don't add adapters. The LLM is the adapter.
- One feature per PR.

## License

By contributing, you agree your code is MIT licensed.
