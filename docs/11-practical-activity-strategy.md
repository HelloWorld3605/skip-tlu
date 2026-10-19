# Practical Activity Strategy

## 1. Practical activity types

### A. Lesson containing theory + practice

Examples use names such as [LÝ THUYẾT + BÀI TẬP THỰC HÀNH] ...

Workflow: Open → navigate pages/branches → reach end → verify completion.

This is not a video-watcher problem.

### B. Assignment: submit a file

Examples include [NỘP BÀI TẬP THỰC HÀNH] and [LUYỆN TẬP KIỂM TRA THỰC HÀNH].

Direct inspection of Assignment 51068 showed:

- Completion requirement: Make a submission
- Add submission
- File submissions
- Word document upload
- Save changes
- Submission status

Handler workflow:

1. Open assignment.
2. Resolve requirements and availability.
3. Prepare/select an artifact.
4. Open Add submission.
5. Upload the file through Moodle's file manager.
6. Save changes.
7. Submit/finalize if a separate submission step is required.
8. Re-open assignment.
9. Verify submission and completion.

Do not equate upload/draft with final submission.

### C. Self-graded practical quiz

Quiz 51560 was inspected. Observed requirements: Receive a grade, Receive a passing grade, 30 minute time limit, unlimited attempts until the passing threshold, grading method Highest grade and passing grade 7/10.

Process: External practical task → Quiz attempt → grade → if grade >= pass, complete → otherwise retry if allowed.

This differs from a quiz that only requires Make an attempt.

### D. Practical exam

Weeks 5, 9, 12 and 13 contain practical exams.

Planner:

Prerequisite complete? → no: BLOCKED → yes: check time window → not open: SCHEDULED → closed: EXPIRED → open: READY.

## 2. Artifact strategy

Do not put document generation inside AssignmentHandler.

Use an ArtifactProvider abstraction with a prepare(activity) operation returning a file path.

Possible providers:

- existing user file
- generated Word file
- generated PowerPoint file
- generated Excel file
- template-based artifact

Then: ArtifactProvider → Moodle Assignment Handler → upload → submit → verify.

## 3. Word

A future WordArtifactProvider can generate DOCX using heading/style, page layout, table of contents, numbering, header/footer and formatting rules. The task/rubric must be the source of truth; assignment IDs should not contain business logic.

## 4. PowerPoint

A future PowerPointArtifactProvider can generate PPTX from slide count, titles, layouts, images, tables/charts and required formatting.

## 5. Excel

A future ExcelArtifactProvider can generate XLSX with worksheets, formulas, formatting, sorting/filtering, charts, structured data and Pivot preparation where appropriate.

## 6. What the engine must not do

Do not set completion directly in the DOM, fake a Done state, upload an empty placeholder just to satisfy a submission, mark completion without server verification, bypass activity restrictions, ignore open/close/due windows or treat an upload draft as a final submission.

## 7. Practical execution contract

A practical handler should expose intermediate states:

- ARTIFACT_PREPARED
- SUBMISSION_CREATED
- SUBMISSION_SUBMITTED
- COMPLETION_VERIFIED

If only uploaded: uploaded=true, submitted=false, completion=INCOMPLETE, reason=SUBMISSION_NOT_FINALIZED.

## 8. Recommended SkipTLU architecture

Separate ProcessPlanner, ArtifactEngine, MoodleActivityEngine and VerificationEngine.

ProcessPlanner understands prerequisites, restrictions and time windows.
ArtifactEngine prepares Word/PPT/Excel artifacts.
MoodleActivityEngine executes Moodle workflows.
VerificationEngine confirms authoritative server state.
