# Architecture

```text
CLI -> Course Discovery -> Activity Model -> Completion Resolver
                                      -> Handler Router
                                         -> Lesson / Quiz / Assignment / Feedback / Resource / Page / H5P
                                      -> Server Verification -> Execution Result
```

## Layers
- `MoodleClient`: HTTP/session boundary.
- `CourseDiscovery`: discovers Moodle activity links.
- Pydantic models: Course, Section, Activity, Requirements.
- `CompletionResolver`: normalizes requirements.
- Handlers: module-specific workflows.
- Verification: authoritative server-side completion check.

Adding a module requires a type, handler, resolver logic and tests.
