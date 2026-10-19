from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlparse

from skiptlu.client.session import AssignmentSubmission, MoodleSession, QuizAttempt, SessionPage
from skiptlu.models.activity import Activity, CompletionStatus
from skiptlu.quiz.models import QuizAnswerPlan, QuizQuestion
from skiptlu.feedback.models import FeedbackResponsePlan, FeedbackQuestion
from skiptlu.quiz.parser import MoodleQuizParser
from skiptlu.feedback.parser import MoodleFeedbackParser
from skiptlu.tasks.context import ActivityAttachment, ActivityContext
from skiptlu.references.parser import ReferenceParser


class PlaywrightMoodleSession:
    """MoodleSession backed by an async Playwright browser.

    The adapter owns browser mechanics; handlers only see the MoodleSession
    contract. Authentication is expected to be supplied through Playwright
    storage state (SKIPTLU_STORAGE_STATE) or an already authenticated context.
    """

    def __init__(
        self,
        *,
        headless: bool = True,
        storage_state: str | Path | None = None,
        base_url: str | None = None,
    ) -> None:
        self.headless = headless
        self.storage_state = Path(
            storage_state or os.getenv("SKIPTLU_STORAGE_STATE", "")
        ) if (storage_state or os.getenv("SKIPTLU_STORAGE_STATE")) else None
        self.base_url = base_url
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._reference_parser = ReferenceParser()

    async def _ensure_page(self):
        if self._page is not None:
            return self._page

        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is required for browser execution. "
                "Install with: pip install 'skiptlu[browser]'"
            ) from exc

        self._playwright = await async_playwright().start()
        launch_kwargs = {"headless": self.headless}

        self._browser = await self._playwright.chromium.launch(**launch_kwargs)
        context_kwargs = {}
        if self.storage_state and self.storage_state.exists():
            context_kwargs["storage_state"] = str(self.storage_state)

        self._context = await self._browser.new_context(**context_kwargs)
        self._page = await self._context.new_page()
        return self._page

    async def open(self, url: str) -> SessionPage:
        page = await self._ensure_page()
        await page.goto(url, wait_until="domcontentloaded")

        # Moodle can offer a resume dialog for lessons. Prefer the server's
        # "last page seen" option rather than restarting the lesson.
        await self._resume_last_seen_if_prompted(page)
        return await self._read_page()

    async def collect_activity_context(self, activity: Activity) -> ActivityContext:
        if not activity.url:
            raise ValueError(f"Activity {activity.id} has no URL")

        page = await self._ensure_page()
        if page.url != activity.url:
            await page.goto(activity.url, wait_until="domcontentloaded")

        payload = await page.evaluate(
            """() => {
                const intro = document.querySelector('#intro');
                const root = intro || document.querySelector('#region-main');
                if (!root) {
                    return {
                        description: '',
                        instructions: [],
                        attachments: [],
                        relatedActivities: [],
                        completion: []
                    };
                }

                const links = [...root.querySelectorAll('a[href]')].map(a => ({
                    name: (a.innerText || a.textContent || '').trim(),
                    url: a.href,
                    content_type: null
                })).filter(x => x.url);

                const paragraphs = [...root.querySelectorAll('p, li')]
                    .map(el => (el.innerText || el.textContent || '').trim())
                    .filter(Boolean);

                const completionRoot = document.querySelector('[data-region="completionrequirements"]');
                const completion = completionRoot
                    ? [...completionRoot.querySelectorAll('[role="listitem"]')]
                        .map(el => (el.innerText || el.textContent || '').trim())
                        .filter(Boolean)
                    : [];

                const titleNode = document.querySelector('.rui-main-content-title, h1, h2, h3, h4');
                return {
                    title: titleNode ? (titleNode.innerText || titleNode.textContent || '').trim() : '',
                    description: root.innerText || '',
                    instructions: paragraphs,
                    attachments: links,
                    relatedActivities: [],
                    completion
                };
            }""",
        )
        collected = payload or {}
        # Keep the canonical activity name discovered from the course. The
        # page heading can be a theme/title such as "Notifications" and is
        # not necessarily the Moodle activity name.
        return ActivityContext.from_collected_data(activity, collected)

    async def download_references(self, context: ActivityContext, output_dir: Path) -> ActivityContext:
        """Download Moodle reference links using the authenticated browser context."""
        if self._context is None:
            await self._ensure_page()
        if self._context is None:
            raise RuntimeError("Playwright context is not initialized")

        output_dir.mkdir(parents=True, exist_ok=True)
        downloaded: dict[str, Path] = {}

        for attachment in context.attachments:
            if not attachment.url:
                continue
            response = await self._context.request.get(attachment.url)
            try:
                if not response.ok:
                    continue
                body = await response.body()
            finally:
                await response.dispose()

            if not body:
                continue

            filename = self._reference_filename(attachment.name, attachment.url)
            target = output_dir / filename
            target.write_bytes(body)
            downloaded[attachment.url] = target

        return context.with_attachment_paths(downloaded)

    @staticmethod
    def _reference_filename(name: str, url: str) -> str:
        candidate = Path(name.strip()).name
        url_name = Path(urlparse(url).path).name
        if not candidate or candidate in {".", ".."}:
            candidate = url_name or "reference"
        elif "." not in candidate and "." in url_name:
            candidate = f"{candidate}_{url_name}"
        candidate = re.sub(r'[<>:"/\\|?*]+', "_", candidate)
        return candidate or "reference"

    async def parse_references(self, context: ActivityContext) -> ActivityContext:
        documents = []
        for attachment in context.attachments:
            if attachment.path is None or not attachment.path.is_file():
                continue
            try:
                documents.append(self._reference_parser.parse(attachment.path))
            except ValueError:
                continue
        return context.with_parsed_references(tuple(documents))

    async def next_page(self) -> SessionPage:
        page = await self._ensure_page()

        form = page.locator("form[action*='/mod/lesson/continue.php']").filter(
            has=page.locator("button")
        )

        buttons = form.locator("button")
        count = await buttons.count()
        if count == 0:
            return await self._read_page()

        target = None
        for index in range(count):
            button = buttons.nth(index)
            text = (await button.inner_text()).strip().lower()
            if text in {"trang tiếp theo", "hoàn thành", "next page", "finish"}:
                target = button
                break

        if target is None:
            target = buttons.last

        await target.click()
        await page.wait_for_load_state("domcontentloaded")
        return await self._read_page()

    async def read_current_html(self) -> str:
        page = await self._ensure_page()
        return await page.content()

    async def read_completion(self, activity: Activity) -> CompletionStatus:
        page = await self._ensure_page()

        selector = f"#course-index-cm-{activity.id} .completioninfo"
        node = page.locator(selector).first

        if await node.count():
            value = await node.get_attribute("data-value")
            classes = await node.get_attribute("class") or ""
            if value == "1" or "completion_complete" in classes:
                return CompletionStatus.COMPLETE

        # Some Moodle themes expose completion in the activity page itself.
        text = (await page.locator("body").inner_text()).lower()
        if "congratulations - end of lesson reached" in text:
            # Re-read the course-index marker after the final transition.
            if await node.count():
                value = await node.get_attribute("data-value")
                if value == "1":
                    return CompletionStatus.COMPLETE

        return CompletionStatus.INCOMPLETE

    async def start_quiz_attempt(self, activity: Activity) -> QuizAttempt:
        if not activity.url:
            raise ValueError(f"Quiz {activity.id} has no URL")

        page = await self._ensure_page()
        await page.goto(activity.url, wait_until="domcontentloaded")

        attempt_link = page.locator(
            "a[href*='/mod/quiz/attempt.php?attempt=']"
        ).first
        if await attempt_link.count():
            href = await attempt_link.get_attribute("href") or ""
            attempt_id = self._query_param(href, "attempt")
            return QuizAttempt(
                activity_id=activity.id,
                attempt_id=attempt_id,
                started=True,
                submitted=False,
                ready_to_submit=False,
            )

        buttons = page.get_by_role("button")
        links = page.get_by_role("link")
        candidates = [buttons, links]
        for locator in candidates:
            for index in range(await locator.count()):
                node = locator.nth(index)
                label = (await node.inner_text()).strip().lower()
                if "attempt quiz" in label or "làm bài kiểm tra" in label or "bắt đầu làm bài" in label:
                    await node.click()
                    await page.wait_for_load_state("domcontentloaded")
                    break
            else:
                continue
            break

        attempt_id = self._query_param(page.url, "attempt")
        started = "/mod/quiz/attempt.php" in page.url and bool(attempt_id)

        return QuizAttempt(
            activity_id=activity.id,
            attempt_id=attempt_id,
            started=started,
            submitted=False,
            ready_to_submit=False,
            status_text="Quiz attempt opened" if started else "Quiz attempt could not be opened",
        )

    async def read_feedback_questions(self, activity: Activity) -> tuple[FeedbackQuestion, ...]:
        if not activity.url:
            raise ValueError(f"Feedback {activity.id} has no URL")
        page = await self._ensure_page()
        await page.goto(activity.url, wait_until="domcontentloaded")
        return MoodleFeedbackParser().parse(await page.content())

    async def fill_feedback_responses(
        self,
        activity: Activity,
        plan: FeedbackResponsePlan,
    ) -> bool:
        questions = await self.read_feedback_questions(activity)
        if not plan.is_complete_for(questions):
            return False

        page = await self._ensure_page()
        for question in questions:
            response = plan.for_question(question.question_id)
            if response is None:
                continue

            for value in response.values:
                base = f"[name='{question.question_id}']"
                control = page.locator(base).first
                if await control.count():
                    tag = await control.evaluate("(el) => el.tagName.toLowerCase()")
                    if tag == "select":
                        await control.select_option(value)
                    elif tag == "textarea" or await control.get_attribute("type") == "text":
                        await control.fill(value)
                    else:
                        option = page.locator(
                            f"[name='{question.question_id}'][value='{value}']"
                        ).first
                        if await option.count():
                            await option.check()
                        else:
                            await control.check()

        return True

    async def submit_feedback(self, activity: Activity) -> CompletionStatus:
        page = await self._ensure_page()
        submit = page.locator(
            "input[type=submit], button[type=submit]"
        ).filter(
            has_text=re.compile(r"submit|gửi|nộp|send|save", re.I)
        ).first

        if not await submit.count():
            submit = page.get_by_role(
                "button",
                name=re.compile(r"submit|gửi|nộp|send|save", re.I),
            ).first

        if not await submit.count():
            return CompletionStatus.INCOMPLETE

        await submit.click()
        await page.wait_for_load_state("domcontentloaded")
        return await self.read_completion(activity)

    async def read_quiz_questions(self, activity: Activity) -> tuple[QuizQuestion, ...]:
        if not activity.url:
            raise ValueError(f"Quiz {activity.id} has no URL")
        page = await self._ensure_page()
        if "/mod/quiz/attempt.php" not in page.url:
            await page.goto(activity.url, wait_until="domcontentloaded")
        return MoodleQuizParser().parse(await page.content())

    async def fill_quiz_answers(self, activity: Activity, plan: QuizAnswerPlan) -> QuizAttempt:
        if not activity.url:
            raise ValueError(f"Quiz {activity.id} has no URL")
        questions = await self.read_quiz_questions(activity)
        if not plan.is_complete_for(questions):
            raise ValueError("Answer plan is incomplete; quiz submission remains blocked")
        page = await self._ensure_page()
        for question in questions:
            answer = plan.for_question(question.question_id)
            if answer is None:
                continue
            for value in answer.values:
                selector = (
                    f"#question-{question.question_id} input[type=radio][value='{value}'], "
                    f"#question-{question.question_id} input[type=checkbox][value='{value}']"
                )
                control = page.locator(selector).first
                if await control.count():
                    await control.check()
                    continue
                text_input = page.locator(
                    f"#question-{question.question_id} input[type=text], "
                    f"#question-{question.question_id} textarea"
                ).first
                if await text_input.count():
                    await text_input.fill(value)
        return QuizAttempt(
            activity_id=activity.id,
            attempt_id=self._query_param(page.url, "attempt"),
            started=True,
            submitted=False,
            ready_to_submit=True,
            status_text="Answer plan applied",
        )

    async def submit_quiz_attempt(self, activity: Activity, attempt: QuizAttempt) -> QuizAttempt:
        if not attempt.ready_to_submit:
            raise ValueError("Quiz attempt is not ready to submit")

        page = await self._ensure_page()
        if attempt.attempt_id and self._query_param(page.url, "attempt") != attempt.attempt_id:
            if activity.url:
                await page.goto(activity.url, wait_until="domcontentloaded")

        finish = page.get_by_role("button", name=re.compile(r"finish attempt|kết thúc", re.I)).first
        if await finish.count():
            await finish.click()
            await page.wait_for_load_state("domcontentloaded")

        confirm = page.get_by_role(
            "button",
            name=re.compile(r"submit all and finish|nộp tất cả và kết thúc|nộp bài", re.I),
        ).first
        if await confirm.count():
            await confirm.click()
            await page.wait_for_load_state("domcontentloaded")

        return await self.read_quiz_result(activity)

    async def read_quiz_result(self, activity: Activity) -> QuizAttempt:
        if not activity.url:
            raise ValueError(f"Quiz {activity.id} has no URL")

        page = await self._ensure_page()
        if "/mod/quiz/" not in page.url or str(activity.id) not in page.url:
            await page.goto(activity.url, wait_until="domcontentloaded")

        body = await page.locator("body").inner_text()
        normalized = " ".join(body.split())

        attempt_id = self._query_param(page.url, "attempt")
        submitted = bool(
            re.search(
                r"submitted|đã nộp|attempt finished|attempt completed|bài làm đã được nộp",
                normalized,
                re.I,
            )
        )

        grade = self._extract_float(
            normalized,
            (
                r"(?:your\s+grade|grade|your\s+score)\s*[:=]\s*([0-9]+(?:[.,][0-9]+)?)",
                r"(?:điểm của bạn|điểm)\s*[:=]\s*([0-9]+(?:[.,][0-9]+)?)",
                r"([0-9]+(?:[.,][0-9]+)?)\s*/\s*10",
            ),
        )
        grade_to_pass = self._extract_float(
            normalized,
            (
                r"grade to pass\s*[:=]\s*([0-9]+(?:[.,][0-9]+)?)",
                r"điểm để đạt\s*[:=]\s*([0-9]+(?:[.,][0-9]+)?)",
            ),
        )

        passed = False
        if grade is not None and grade_to_pass is not None:
            passed = grade >= grade_to_pass
        elif re.search(r"\bpassed\b|\bpass\b|\bđạt\b|\bđã đạt\b", normalized, re.I) and not re.search(
            r"\bnot\s+passed\b|\bnot\s+pass\b|\bkhông\s+đạt\b|\bchưa\s+đạt\b",
            normalized,
            re.I,
        ):
            passed = True

        return QuizAttempt(
            activity_id=activity.id,
            attempt_id=attempt_id,
            started=bool(attempt_id) or "/mod/quiz/" in page.url,
            submitted=submitted,
            grade=grade,
            grade_to_pass=grade_to_pass,
            passed=passed,
            ready_to_submit=False,
            status_text=normalized[:500],
        )

    @staticmethod
    def _query_param(url: str, name: str) -> str | None:
        from urllib.parse import parse_qs, urlparse

        values = parse_qs(urlparse(url).query).get(name)
        return values[0] if values else None

    @staticmethod
    def _extract_float(text: str, patterns: tuple[str, ...]) -> float | None:
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                try:
                    return float(match.group(1).replace(",", "."))
                except ValueError:
                    continue
        return None

    async def submit_assignment(self, activity: Activity, artifact_path: Path) -> AssignmentSubmission:
        if not activity.url:
            raise ValueError(f"Assignment {activity.id} has no URL")
        if not artifact_path.is_file() or artifact_path.stat().st_size == 0:
            raise ValueError("Assignment artifact must exist and be non-empty")

        page = await self._ensure_page()
        edit_url = activity.url + ("&" if "?" in activity.url else "?") + "action=editsubmission"
        await page.goto(edit_url, wait_until="domcontentloaded")

        # Moodle's File Manager uses a real file input inside the repository
        # dialog. Clicking Add... opens the dialog and exposes repo_upload_file.
        add_button = page.locator("a[title='Add...']").first
        if await add_button.count():
            await add_button.click()
            file_input = page.locator("input[type=file][name='repo_upload_file']").first
            await file_input.set_input_files(str(artifact_path))

            upload_button = page.get_by_role("button", name="Upload this file")
            if await upload_button.count():
                await upload_button.click()
            else:
                raise RuntimeError("Moodle File Manager upload button was not found")

            await page.wait_for_timeout(500)

        # Save changes is the actual assignment submission mutation.
        save = page.locator("#id_submitbutton").first
        if not await save.count():
            raise RuntimeError("Moodle assignment Save changes button was not found")
        await save.click()
        # Moodle may save the assignment through a form navigation or an
        # asynchronous theme handler. Do not wait indefinitely for a load event.
        await page.wait_for_timeout(1500)

        return await self.read_assignment_submission(activity)

    async def read_assignment_submission(self, activity: Activity) -> AssignmentSubmission:
        page = await self._ensure_page()
        if activity.url and not page.url.startswith(activity.url):
            await page.goto(activity.url, wait_until="domcontentloaded")

        main = page.locator("#region-main").first
        text = await main.inner_text()
        files = tuple(
            (
                await main.locator("a").all_inner_texts()
            )
        )
        files = tuple(name.strip() for name in files if name.strip().lower().endswith((".docx", ".doc")))

        has_submission = "Submitted for grading" in text or bool(files)
        completion_nodes = main.locator(".rui-completion-info, .completioninfo")
        completion_text = ""
        for i in range(await completion_nodes.count()):
            value = (await completion_nodes.nth(i).inner_text()).strip()
            if "Make a submission" in value:
                completion_text = value
                break

        completion = (
            CompletionStatus.COMPLETE
            if has_submission and "Make a submission" in completion_text
            else CompletionStatus.INCOMPLETE
        )

        return AssignmentSubmission(
            activity_id=activity.id,
            has_submission=has_submission,
            files=files,
            status_text="Submitted for grading" if "Submitted for grading" in text else completion_text,
            completion=completion,
        )

    async def save_storage_state(self, path: Path) -> None:
        page = await self._ensure_page()
        if self._context is None:
            raise RuntimeError("Playwright context is not initialized")
        path.parent.mkdir(parents=True, exist_ok=True)
        await self._context.storage_state(path=str(path))

    async def close(self) -> None:
        if self._context is not None:
            await self._context.close()
        if self._browser is not None:
            await self._browser.close()
        if self._playwright is not None:
            await self._playwright.stop()

        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None

    async def _resume_last_seen_if_prompted(self, page) -> None:
        body = (await page.locator("body").inner_text()).lower()
        markers = (
            "last page you saw",
            "trang cuối bạn đã xem",
            "tiếp tục từ trang cuối",
        )
        if not any(marker in body for marker in markers):
            return

        candidates = page.get_by_role("button")
        count = await candidates.count()
        for index in range(count):
            button = candidates.nth(index)
            text = (await button.inner_text()).strip().lower()
            if text in {"yes", "có", "tiếp tục", "continue"}:
                await button.click()
                await page.wait_for_load_state("domcontentloaded")
                return

        links = page.get_by_role("link")
        count = await links.count()
        for index in range(count):
            link = links.nth(index)
            text = (await link.inner_text()).strip().lower()
            if text in {"yes", "có", "tiếp tục", "continue"}:
                await link.click()
                await page.wait_for_load_state("domcontentloaded")
                return

    async def _read_page(self) -> SessionPage:
        page = await self._ensure_page()
        url = page.url
        title = await page.title()
        body = (await page.locator("body").inner_text()).lower()

        buttons = page.locator("form[action*='/mod/lesson/continue.php'] button")
        labels = []
        for index in range(await buttons.count()):
            labels.append((await buttons.nth(index).inner_text()).strip().lower())

        has_next = any(
            label in {"trang tiếp theo", "next page"}
            for label in labels
        )
        is_final = (
            "congratulations - end of lesson reached" in body
            or any(label in {"hoàn thành", "finish"} for label in labels)
            and not has_next
        )

        return SessionPage(
            url=url,
            title=title,
            has_next=has_next,
            is_final=is_final,
        )
