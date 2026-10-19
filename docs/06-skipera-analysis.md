# Skipera Analysis

Skipera is the architectural reference for SkipTLU. Useful concepts to carry over:

- modular architecture
- CLI
- authentication boundary
- course retrieval
- progress routing
- processing modules
- assessment/discussion separation
- LLM boundary
- Pydantic/domain models

Do **not** copy Coursera-specific GraphQL queries, progress models, watcher logic or assessment APIs. Moodle has a different plugin/activity/completion model.

The reusable abstraction is:

```text
Platform Client -> Course Discovery -> Activity Model -> Completion Resolver -> Module Handler -> Verification
```

The key difference is that SkipTLU is completion-rule driven, not video-watcher driven.
