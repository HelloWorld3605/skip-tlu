# Course-wide Tracking Analysis

## Scope

The analysis was expanded from Week 3 to Weeks 1–15 of ELE1101: Năng lực số và Công nghệ văn phòng.

| Week | Section ID | Topic |
|---:|---:|---|
| 1 | 17907 | Sử dụng máy tính cơ bản |
| 2 | 17910 | Làm quen với Word và Soạn thảo văn bản |
| 3 | 17913 | Định dạng văn bản có nhiều chương, mục |
| 4 | 17916 | Luyện tập định dạng văn bản có nhiều chương, mục |
| 5 | 17917 | Kiểm tra định dạng văn bản có nhiều chương, mục |
| 6 | 17923 | Làm quen với PowerPoint |
| 7 | 17936 | Kỹ năng tạo bài thuyết trình |
| 8 | 17939 | Luyện tập kỹ năng tạo bài thuyết trình |
| 9 | 17940 | Kiểm tra kỹ năng tạo bài thuyết trình |
| 10 | 17920 | Kỹ năng CNTT cơ bản |
| 11 | 17946 | Làm quen với Excel |
| 12 | 17949 | Các hàm cơ bản trong Excel |
| 13 | 17952 | Xử lý dữ liệu và tạo báo cáo trong Excel |
| 14 | 17943 | Pháp luật trong môi trường số |
| 15 | 17955 | Luyện thi |

## Tracking mechanisms

### 1. Activity completion

Activities expose states such as To do and Done. The actual mechanism differs by module.

### 2. Activity restriction / dependency

A major pattern is:

Not available unless: The activity X is marked complete

Example:

Lesson A → marked complete → Lesson B becomes available → marked complete → Quiz becomes available.

This means SkipTLU needs an availability/dependency graph, not just an activity list.

### 3. Manual Mark as done

Some course items expose Mark as done. The engine must distinguish server-confirmed completion, manual completion, view-based completion, grade-based completion and submission-based completion.

### 4. Time windows

Assessment activities expose Opened / Closed / Due information. The engine should model SCHEDULED, READY, EXPIRED and LOCKED_BY_DEPENDENCY instead of treating unavailable activities as errors.

## Patterns by week

### Weeks 1–2

Main pattern: Lesson → Practice Quiz → Weekly Graded Quiz → Feedback.

Week 2 introduces practical self-graded quizzes and Assignment activity.

### Weeks 3–5: Word

Theory/Lesson → Practice Assignment → Practice Quiz → Practical-test practice → Practical exam.

Week 5's practical exam is restricted until the Week 4 practice activity is complete.

### Weeks 6–9: PowerPoint

Theory + Practice → Submission → Practice Quiz → next Theory + Practice → Submission → Practice Quiz → Aggregate practical → Weekly quiz → Practical exam.

Week 7 also introduces H5P/video-guidance style learning.

### Week 10

Mostly a chained lesson/quiz sequence: Lesson → Lesson → Lesson → Quiz → next topic.

### Weeks 11–13: Excel

Theory + Practice → Assignment submission → Practice quiz → next Theory + Practice → Assignment submission → Practice quiz → Aggregate practical → Aggregate quiz → Weekly graded quiz → Feedback → Practical exam.

Week 13 additionally contains Chart and Pivot activities.

### Week 14

Mostly chained quizzes: Theory → Quiz 1 → Quiz 2 → Quiz 3 → Quiz 4 → Weekly graded quiz.

### Week 15

Preparation stage: repeat Week 3 exercises, repeat Week 4 exercises and complete ĐỀ THI THỬ.

## Architectural consequence

SkipTLU should evolve from Activity → Handler to Activity → Preconditions → Process Planner → Handler → Postconditions → Verification.

The course is a workflow graph enforced by completion, restrictions, deadlines and grades.
