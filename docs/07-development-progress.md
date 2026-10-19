# Development Progress

## Version
`0.1.0`

## Done
- Project bootstrap at `D:\LearningPesonal\Project\skiptlu`.
- `pyproject.toml`, README, gitignore.
- Pydantic models for activity/course/completion.
- `CompletionResolver` and `CompletionEngine`.
- Handler base + handlers for lesson, quiz, assign, feedback, resource, page, H5P.
- Handler router.
- Async `MoodleClient` using httpx.
- HTML-based `CourseDiscovery` using BeautifulSoup.
- Typer CLI with `inspect` and `architecture` commands.
- Initial unit tests.
- Documentation folder and analysis documents.
- Expanded course analysis from Week 3 to Weeks 1–15.
- Identified Moodle activity-restriction dependency chains.
- Identified manual Mark as done states and time-window states.
- Inspected practical Assignment submission flow and self-graded practical Quiz requirements.
- Added course-wide tracking analysis and practical-activity strategy.

## Latest test
`2 passed in 0.09s`

## Not done yet
- Authenticated Moodle session persistence.
- Real completion metadata parser.
- Authoritative completion-state API/parser.
- Real lesson workflow.
- Quiz attempt/answer/submit workflow.
- Assignment upload/submission.
- Feedback submission.
- H5P completion.
- Robust course-wide discovery.
- Network/request tracing.
- Retry/rate limiting/error handling.
- Persistent progress/reporting.
- ELMS-TLU integration tests.

Current handlers intentionally do not fake completion; they are scaffolding.
