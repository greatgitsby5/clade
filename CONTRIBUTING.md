# Contributing to Parley

## What We Need Most

1. **Adapters** — Write a reader/writer for your agent's memory format (SQLite, Markdown, YAML, Letta, LangChain, etc.)
2. **Real-world testing** — Sync your actual agent memories, report what breaks
3. **Edge cases** — Find the conflicts that confuse the LLM

## Writing an Adapter

```python
from parley import MemoryAdapter

class MyAdapter(MemoryAdapter):
    def read(self, path: str) -> list[dict]:
        # Read your format, return list of {"content": "...", "type": "...", ...}
        ...

    def write(self, path: str, memories: list[dict]):
        # Write merged memories back in your format
        ...
```

Use it:
```bash
python parley.py --store-a file.json --store-b custom.db --adapter-b my_adapter.MyAdapter
```

## Pull Requests

- Keep it simple. Parley is ~200 lines for a reason.
- Test with real memory files if possible.
- One feature per PR.

## License

By contributing, you agree your code is MIT licensed.
