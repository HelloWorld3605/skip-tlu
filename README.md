# SkipTLU

Moodle/ELMS activity-progress engine inspired by the architecture study of Skipera.

## Goal

Automate and verify learner progress in Moodle-based ELMS systems without hard-coding a single course or activity ID.

The first target is ELMS-TLU and its Moodle activity-completion model.

## Architecture

```
CLI
 └── Course Discovery
      └── Activity
           └── Completion Resolver
                └── Handler Router
                     ├── Lesson
                     ├── Quiz
                     ├── Assignment
                     ├── Feedback
                     ├── Resource/Page
                     └── H5P
                          ↓
                    Server Verification
```

## Important design rule

Executing an action does **not** mean the activity is completed.

Every handler must:

1. inspect the current activity/completion state;
2. resolve the requirements;
3. perform the minimum valid workflow;
4. verify the server-side completion state;
5. report the resulting state.

## Current ELMS-TLU observations

The Week 3 course contains:

- Lesson: 51014, 51023, 51026
- Assignment: 51017, 51032
- Resource: 51029
- Quiz: 51567, 51545
- Feedback: 51038, 51053

The project intentionally does not hard-code these IDs.

## Development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
pytest
skiptlu --help
```

Authentication and real completion mutations are intentionally isolated behind the client/handler interfaces. This prevents the core engine from depending on browser-specific behavior.
