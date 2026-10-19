# Roadmap

## Phase 1 — Foundation — DONE
Package, models, router, completion engine, discovery scaffold, CLI, tests, documentation.

## Phase 2 — Moodle State — NEXT
1. Authenticated browser/session boundary.
2. Parse Moodle completion UI/state.
3. Parse Activity Restriction / prerequisite dependencies.
4. Parse Opened / Closed / Due availability windows.
5. Identify reliable completion state source.
6. Normalize real requirements.
7. Build completion + availability snapshots.

## Phase 3 — Process + Module Handlers
1. ProcessPlanner for prerequisites, restrictions and time windows.
2. Resource/Page -> Lesson -> Feedback -> Assignment -> Quiz -> H5P.
3. ArtifactProvider for practical Word/PPT/Excel files.
4. Assignment lifecycle: prepare -> upload -> save -> submit -> verify.
5. Quiz grade/passing-grade workflow.

## Phase 4 — Process Tracking
Course -> Section -> Activity -> Preconditions -> Action -> Postconditions -> Verification -> Result.

## Phase 5 — ELMS-TLU Integration
Authenticated session, Week 3 integration test, practical Assignment test, practical Quiz test, real completion verification, false-positive checks and diagnostics.

## Phase 6 — CLI/UX
Potential commands: course inspect, activity inspect, progress, process, verify and graph.

## Phase 7 — Advanced
Retry policy, rate limiting, persistence, concurrency, dry-run, audit log and optional LLM-assisted interpretation.
