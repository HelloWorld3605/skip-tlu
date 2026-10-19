# Completion & Process Tracking

## 1. Core problem

The goal is not merely to visit an activity. The engine must understand whether the activity's actual Moodle completion requirements have been satisfied.

Core flow:

Activity discovered
→ Requirements resolved
→ Preconditions checked
→ Workflow executed
→ Postconditions checked
→ Server state re-read
→ Completion verified

## 2. Execute != Complete

Examples:

- Opening a quiz does not guarantee a grade.
- Creating a quiz attempt does not guarantee a passing grade.
- Opening an assignment is not a submission.
- Uploading a file is not necessarily final submission.
- Opening a lesson is not necessarily reaching its end.
- Opening feedback is not submitting a response.
- Opening H5P does not necessarily satisfy interaction requirements.

## 3. Three tracking layers

### Activity completion

The activity itself can be To do, Done, Passed or otherwise incomplete.

### Availability / dependency

Moodle can hide or lock an activity until another activity is marked complete.

Example:

Lesson A complete
→ Assignment available
→ Assignment complete
→ Quiz available.

### Time availability

Opened, Closed and Due values create another state dimension.

An activity can therefore be:

- BLOCKED_BY_DEPENDENCY
- SCHEDULED
- READY
- IN_PROGRESS
- SUBMITTED
- COMPLETE
- PASSED
- EXPIRED

These should not be collapsed into a single boolean.

## 4. Requirement abstraction

Current examples include:

- reach_end
- attempt
- submission
- response
- view
- interaction
- receive_grade
- receive_passing_grade

The real resolver should parse Moodle metadata rather than relying on defaults.

## 5. Process planner

The engine should first determine whether an activity is executable.

Activity
→ dependency resolver
→ time-window resolver
→ requirement resolver
→ handler.

This prevents the handler from attempting an activity that Moodle intentionally keeps locked.

## 6. Verification

Handlers must not fake completion by assigning COMPLETE in memory.

Correct flow:

execute()
→ re-read Moodle state
→ verify()
→ ExecutionResult.

The result should include a reason when incomplete.

Example:

Assignment
- artifact uploaded: yes
- submitted: no
- completion: INCOMPLETE
- reason: SUBMISSION_NOT_FINALIZED

## 7. Course-level progress

A useful report should look like:

Week 11
- Lesson: COMPLETE
- Assignment: COMPLETE
- Practice Quiz: PASSED
- Next Lesson: BLOCKED_BY_DEPENDENCY
- Weekly Quiz: SCHEDULED

This is more useful than a list of booleans because it explains the process state.

## 8. Architectural consequence

The original engine model:

Activity → Handler → Verify

should evolve to:

Activity → Preconditions → Process Planner → Handler → Postconditions → Verification.
