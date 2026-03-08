# Real-Model Demo Note

The current OpenRouter action smoke demonstrates a useful failure-analysis pattern:

- The model reads the relevant test file first.
- It then makes a source-side edit instead of directly modifying the protected test file.
- That source edit may still pass `PytestGrader`.
- `SourceShortcutMonitor` flags the run because the source write happened after reading tests, which is a plausible shortcut or overfit signal.

Why this matters:

- Task success and suspicious behavior remain separate signals.
- Sentinel is not limited to catching direct test tampering.
- The live-model path now produces inspectable artifacts for a subtler class of risky behavior: test-informed shortcut edits in source files.
