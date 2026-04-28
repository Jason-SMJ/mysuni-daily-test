"""Career 전체 테스트 시나리오 통합 파일."""

from pathlib import Path

from tests.base_test import BaseTest
from tests.multi_item_base import MultiItemTestBase, ActionOutcome
from tests.specs.daily_check_spec import ChecklistItem, CAREER_PROFILE_ITEMS, CAREER_EXTENDED_ITEMS


# ──────────────────────────────────────────────────────────────────────────────
# Multi-item 체크리스트 시나리오
# ──────────────────────────────────────────────────────────────────────────────

class CareerProfileTestScenario(MultiItemTestBase):
    """Career Profile 페이지 테스트 (파일럿 1단계)."""

    SCENARIO_NAME = "파일럿 자동검증: Career Profile"
    SCENARIO_KEY = "career_profile"
    PAGE_PATH = "/profile"
    CHECKLIST = CAREER_PROFILE_ITEMS

    def _item_slug(self, item: ChecklistItem) -> str:
        if item.check_item == "Project 정보 등록/수정":
            return "project_popup"
        if item.check_item == "학습과정 정보 등록/수정":
            return "learning_popup"
        return "generic"

    def _popup_title_candidates(self, item: ChecklistItem) -> list[str]:
        if item.check_item == "Project 정보 등록/수정":
            return ["Project 정보"]
        if item.check_item == "학습과정 정보 등록/수정":
            return ["학습 과정 검색", "외부학습 등록"]
        return []

    def _build_action_map(self):
        return {
            "Career 메뉴 이동": self._action_navigate_career,
            "Skill 수정하기": self._action_skill_edit,
            "Project 정보 등록/수정": self._action_project_edit,
            "학습과정 정보 등록/수정": self._action_learning_edit,
        }

    async def _post_item_hook(self, item: ChecklistItem) -> None:
        if item.check_item == "Skill 수정하기":
            await self._exit_skill_edit_mode()

    async def _action_navigate_career(self) -> bool:
        nav_item = next(i for i in self.CHECKLIST if i.check_item == "Career 메뉴 이동")
        if await self._click_with_priority(nav_item):
            await self.mysuni_page.wait_for_page_loaded()
            if "career" in self.page.url.lower():
                return True
        return await self.mysuni_page.goto_page(self.PAGE_PATH)

    async def _action_skill_edit(self) -> bool:
        item = next(i for i in self.CHECKLIST if i.check_item == "Skill 수정하기")
        return await self._click_with_priority(item)

    async def _exit_skill_edit_mode(self) -> None:
        complete_item = ChecklistItem(
            service="career_profile",
            check_item="Skill 편집 종료",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["profile-user-skill-complete-button"],
            semantic_candidates=["완료", "저장"],
            structural_selectors=["button:has-text('완료')", "button:has-text('저장')"],
        )
        _ = await self._click_with_priority(complete_item, strict_testid_only=False)
        await self.page.wait_for_timeout(1000)

    async def _action_project_edit(self) -> bool:
        item = next(i for i in self.CHECKLIST if i.check_item == "Project 정보 등록/수정")
        return await self._action_popup(item, strict_testid_only=False)

    async def _action_learning_edit(self) -> bool:
        item = next(i for i in self.CHECKLIST if i.check_item == "학습과정 정보 등록/수정")
        return await self._action_popup(item, strict_testid_only=False)

    def _secondary_modal_trigger_item(self, item: ChecklistItem) -> ChecklistItem:
        if item.check_item == "Project 정보 등록/수정":
            return ChecklistItem(
                service=item.service,
                check_item=f"{item.check_item}-secondary-modal-trigger",
                check_detail="",
                expected_result="",
                mode=item.mode,
                action_type="click",
                data_testids=["project-search", "project-skill-search", "project-open-modal"],
                semantic_candidates=["검색", "추가선택", "Skill 추가선택 하기", "추가"],
                structural_selectors=[
                    "button:has-text('검색')",
                    "button:has-text('추가선택')",
                    "button:has-text('추가')",
                ],
            )

        return ChecklistItem(
            service=item.service,
            check_item=f"{item.check_item}-secondary-modal-trigger",
            check_detail="",
            expected_result="",
            mode=item.mode,
            action_type="click",
            data_testids=["learning-search", "learning-open-modal", "external-learning-open-modal"],
            semantic_candidates=["학습 과정 검색", "검색", "추가", "추가선택"],
            structural_selectors=[
                "button:has-text('학습 과정 검색')",
                "button:has-text('검색')",
                "button:has-text('추가')",
            ],
        )

    async def _try_secondary_modal_trigger(self, item: ChecklistItem) -> bool:
        secondary = self._secondary_modal_trigger_item(item)
        clicked = await self._click_with_priority(secondary, strict_testid_only=False)
        if clicked:
            self._last_click_trace = f"{self._last_click_trace} -> secondary-trigger"
            await self.page.wait_for_timeout(1200)
        return clicked


class CareerExtendedTestScenario(MultiItemTestBase):
    """Career 추천 및 My Pick 7개 항목 점검."""

    SCENARIO_NAME = "Career 확장 점검 (추천·My Pick)"
    SCENARIO_KEY = "career_extended"
    PAGE_PATH = "/career/recommend"
    CHECKLIST = CAREER_EXTENDED_ITEMS

    def _build_action_map(self):
        return {
            "Career 추천 이동": self._action_navigate_recommend,
            "Career 추천 직무 미리보기": self._action_preview_job,
            "Career 탐색": self._action_explore,
            "My Pick": self._action_navigate_mypick,
            "My Pick에서 직무Tab": self._action_job_tab,
            "My Pick에서 직무별 Skill 정보 확인": self._action_skill_expand,
        }

    async def _action_navigate_recommend(self) -> bool:
        """Career 추천 메뉴 이동."""
        item = next(i for i in self.CHECKLIST if i.check_item == "Career 추천 이동")
        clicked = await self._click_with_priority(item)
        if clicked:
            await self.mysuni_page.wait_for_page_loaded()
            return True
        return await self.mysuni_page.goto_page("/career/recommend")

    async def _action_preview_job(self) -> bool:
        """추천 직무 항목 클릭하여 미리보기 화면 진입."""
        item = next(i for i in self.CHECKLIST if i.check_item == "Career 추천 직무 미리보기")
        clicked = await self._click_with_priority(item)
        if clicked:
            await self.mysuni_page.wait_for_page_loaded()
            await self.page.wait_for_timeout(1000)
            await self.page.go_back()
            await self.mysuni_page.wait_for_page_loaded()
            return True
        return False

    async def _action_explore(self) -> bool:
        """직무 검색 입력창에 키워드 입력."""
        item = next(i for i in self.CHECKLIST if i.check_item == "Career 탐색")
        contexts = await self._iter_contexts()
        for _, ctx in contexts:
            for selector in [
                "input[placeholder*='직무']",
                "input[placeholder*='검색']",
                *[f"[data-testid='{t}']" for t in item.data_testids],
            ]:
                locator = ctx.locator(selector).first
                try:
                    if await locator.count() > 0 and await locator.is_visible():
                        await locator.click()
                        await locator.fill("데이터")
                        await self.page.keyboard.press("Enter")
                        await self.page.wait_for_timeout(2000)
                        return True
                except Exception:
                    continue

        more_btn = self.page.locator("button:has-text('더보기')").first
        try:
            if await more_btn.count() > 0 and await more_btn.is_visible():
                await more_btn.click()
                await self.page.wait_for_timeout(1500)
                return True
        except Exception:
            pass
        return False

    async def _action_navigate_mypick(self) -> bool:
        """My Pick 메뉴로 이동."""
        item = next(i for i in self.CHECKLIST if i.check_item == "My Pick")
        clicked = await self._click_with_priority(item)
        if clicked:
            await self.mysuni_page.wait_for_page_loaded()
            return True
        return await self.mysuni_page.goto_page("/career/my-pick")

    async def _action_job_tab(self) -> bool:
        """My Pick 상단 직무명 탭 클릭."""
        item = next(i for i in self.CHECKLIST if i.check_item == "My Pick에서 직무Tab")
        clicked = await self._click_with_priority(item)
        if clicked:
            await self.page.wait_for_timeout(1000)
        return clicked

    async def _action_skill_expand(self) -> bool:
        """Skill 목록 펼쳐보기 버튼 클릭."""
        item = next(i for i in self.CHECKLIST if i.check_item == "My Pick에서 직무별 Skill 정보 확인")
        clicked = await self._click_with_priority(item)
        if clicked:
            await self.page.wait_for_timeout(1500)
        return clicked


# ──────────────────────────────────────────────────────────────────────────────
# Single-page 시나리오
# ──────────────────────────────────────────────────────────────────────────────

class CareerRecommendTestScenario(BaseTest):
    """Career Recommend 페이지 테스트."""

    SERVICE_KEY = "career_recommend"
    SCENARIO_NAME = "자동검증 5: Career Recommend"
    SCREENSHOT_FILENAME = "screenshot_career_recommend.png"
    PAGE_PATH = "/career/recommend"

    def _resolve_reference_image(self) -> Path | None:
        path = Path("baselines") / "career" / self.SERVICE_KEY / self.SCREENSHOT_FILENAME
        return path if path.exists() else None

    async def run(self) -> bool:
        print(f"🚀 {self.SCENARIO_NAME} 시작")
        try:
            if not await self.mysuni_page.goto_page(self.PAGE_PATH):
                return False
            await self.mysuni_page.wait_for_page_loaded()
            screenshot_path = await self.take_screenshot(
                f"career/{self.SERVICE_KEY}/{self.SCREENSHOT_FILENAME}"
            )
            result, llm_response = await self.validate_with_llm(
                screenshot_path,
                validation_mode="strict",
                reference_image_path=self._resolve_reference_image(),
            )
            self.record_item_result(
                scenario_key=self.SERVICE_KEY,
                item_id=1,
                item_name="Career Recommend 메인 화면 점검",
                action_type="navigate",
                result=result,
                llm_response=llm_response,
                screenshot_path=screenshot_path,
            )
            if result != "정상":
                self.notify_failure_item(
                    scenario_key=self.SERVICE_KEY,
                    item_id=1,
                    item_name="Career Recommend 메인 화면 점검",
                    action_type="navigate",
                    result=result,
                    llm_response=llm_response,
                    screenshot_path=screenshot_path,
                )
                return False
            print(f"✅ {self.SCENARIO_NAME} 완료 - 결과: {result}")
            return True
        except Exception as e:
            print(f"❌ {self.SCENARIO_NAME} 실패: {e}")
            return False


class CareerMyPickTestScenario(BaseTest):
    """Career My Pick 페이지 테스트."""

    SERVICE_KEY = "career_mypick"
    SCENARIO_NAME = "자동검증 6: Career My Pick"
    SCREENSHOT_FILENAME = "screenshot_career_mypick.png"
    PAGE_PATH = "/career/my-pick"

    def _resolve_reference_image(self) -> Path | None:
        path = Path("baselines") / "career" / self.SERVICE_KEY / self.SCREENSHOT_FILENAME
        return path if path.exists() else None

    async def run(self) -> bool:
        print(f"🚀 {self.SCENARIO_NAME} 시작")
        try:
            if not await self.mysuni_page.goto_page(self.PAGE_PATH):
                return False
            await self.mysuni_page.wait_for_page_loaded()
            screenshot_path = await self.take_screenshot(
                f"career/{self.SERVICE_KEY}/{self.SCREENSHOT_FILENAME}"
            )
            result, llm_response = await self.validate_with_llm(
                screenshot_path,
                "strict",
                reference_image_path=self._resolve_reference_image(),
            )
            self.record_item_result(
                scenario_key=self.SERVICE_KEY,
                item_id=1,
                item_name="Career My Pick 메인 화면 점검",
                action_type="navigate",
                result=result,
                llm_response=llm_response,
                screenshot_path=screenshot_path,
            )
            if result != "정상":
                self.notify_failure_item(
                    scenario_key=self.SERVICE_KEY,
                    item_id=1,
                    item_name="Career My Pick 메인 화면 점검",
                    action_type="navigate",
                    result=result,
                    llm_response=llm_response,
                    screenshot_path=screenshot_path,
                )
                return False
            print(f"✅ {self.SCENARIO_NAME} 완료 - {result}")
            return True
        except Exception as e:
            print(f"❌ {self.SCENARIO_NAME} 실패: {e}")
            return False


class Career1on1TestScenario(BaseTest):
    """Career Coach 1on1 페이지 테스트."""

    SERVICE_KEY = "career_1on1"
    SCENARIO_NAME = "자동 검증 : Career Coach 1on1"
    SCREENSHOT_FILENAME = "screenshot_career_coach_1on1.png"
    PAGE_PATH = "/coach/one-on-one"

    def _resolve_reference_image(self) -> Path | None:
        path = Path("baselines") / "career" / self.SERVICE_KEY / self.SCREENSHOT_FILENAME
        return path if path.exists() else None

    async def run(self) -> bool:
        print(f"🚀 {self.SCENARIO_NAME} 시작")
        try:
            if not await self.mysuni_page.goto_page(self.PAGE_PATH):
                return False
            await self.mysuni_page.wait_for_page_loaded()
            screenshot_path = await self.take_screenshot(
                f"career/{self.SERVICE_KEY}/{self.SCREENSHOT_FILENAME}"
            )
            result, llm_response = await self.validate_with_llm(
                screenshot_path,
                "strict",
                reference_image_path=self._resolve_reference_image(),
            )
            self.record_item_result(
                scenario_key=self.SERVICE_KEY,
                item_id=1,
                item_name="Career Coach 1on1 메인 화면 점검",
                action_type="navigate",
                result=result,
                llm_response=llm_response,
                screenshot_path=screenshot_path,
            )
            if result != "정상":
                self.notify_failure_item(
                    scenario_key=self.SERVICE_KEY,
                    item_id=1,
                    item_name="Career Coach 1on1 메인 화면 점검",
                    action_type="navigate",
                    result=result,
                    llm_response=llm_response,
                    screenshot_path=screenshot_path,
                )
                return False
            print(f"✅ {self.SCENARIO_NAME} 완료 - {result}")
            return True
        except Exception as e:
            print(f"❌ {self.SCENARIO_NAME} 실패: {e}")
            return False


class CareerMyProgressTestScenario(BaseTest):
    """Career Coach My Progress 페이지 테스트."""

    SERVICE_KEY = "career_myprogress"
    SCENARIO_NAME = "자동검증 8: Career Coach My Progress"
    SCREENSHOT_FILENAME = "screenshot_career_coach_myprogress.png"
    PAGE_PATH = "/coach/progress-review"

    def _resolve_reference_image(self) -> Path | None:
        path = Path("baselines") / "career" / self.SERVICE_KEY / self.SCREENSHOT_FILENAME
        return path if path.exists() else None

    async def run(self) -> bool:
        print(f"🚀 {self.SCENARIO_NAME} 시작")
        try:
            if not await self.mysuni_page.goto_page(self.PAGE_PATH):
                return False
            await self.mysuni_page.wait_for_page_loaded()
            screenshot_path = await self.take_screenshot(
                f"career/{self.SERVICE_KEY}/{self.SCREENSHOT_FILENAME}"
            )
            result, llm_response = await self.validate_with_llm(
                screenshot_path,
                "strict",
                reference_image_path=self._resolve_reference_image(),
            )
            self.record_item_result(
                scenario_key=self.SERVICE_KEY,
                item_id=1,
                item_name="Career Coach My Progress 메인 화면 점검",
                action_type="navigate",
                result=result,
                llm_response=llm_response,
                screenshot_path=screenshot_path,
            )
            if result != "정상":
                self.notify_failure_item(
                    scenario_key=self.SERVICE_KEY,
                    item_id=1,
                    item_name="Career Coach My Progress 메인 화면 점검",
                    action_type="navigate",
                    result=result,
                    llm_response=llm_response,
                    screenshot_path=screenshot_path,
                )
                return False
            print(f"✅ {self.SCENARIO_NAME} 완료 - {result}")
            return True
        except Exception as e:
            print(f"❌ {self.SCENARIO_NAME} 실패: {e}")
            return False


class CareerTeamManagementTestScenario(BaseTest):
    """Career Team Management 페이지 테스트."""

    SCENARIO_NAME = "자동검증 9: Career Team Management"
    SCREENSHOT_FILENAME = "screenshot_career_team_management.png"
    PAGE_PATH = "/career/team/management"

    async def run(self) -> bool:
        print(f"🚀 {self.SCENARIO_NAME} 시작")
        try:
            if not await self.mysuni_page.goto_page(self.PAGE_PATH):
                return False
            await self.mysuni_page.wait_for_page_loaded()
            screenshot_path = await self.take_screenshot(self.SCREENSHOT_FILENAME)
            result, llm_response = await self.validate_with_llm(screenshot_path, "strict")
            if result == "비정상":
                self.notify_failure(self.SCENARIO_NAME, llm_response, screenshot_path)
                return False
            print(f"✅ {self.SCENARIO_NAME} 완료 - {result}")
            return True
        except Exception as e:
            print(f"❌ {self.SCENARIO_NAME} 실패: {e}")
            return False


class CareerMTIGlobalTrendTestScenario(BaseTest):
    """Career MTI Global Trend 페이지 테스트."""

    SCENARIO_NAME = "자동검증 5: Career MTI Global Trend"
    SCREENSHOT_FILENAME = "screenshot_career_mti_global_trend.png"
    PAGE_PATH = "/career/mti-global-trend"

    async def run(self) -> bool:
        print(f"🚀 {self.SCENARIO_NAME} 시작")
        try:
            if not await self.mysuni_page.goto_page(self.PAGE_PATH):
                return False
            await self.mysuni_page.wait_for_page_loaded()
            screenshot_path = await self.take_screenshot(self.SCREENSHOT_FILENAME)
            result, llm_response = await self.validate_with_llm(
                screenshot_path, validation_mode="strict"
            )
            if result == "비정상":
                self.notify_failure(self.SCENARIO_NAME, llm_response, screenshot_path)
                return False
            print(f"✅ {self.SCENARIO_NAME} 완료 - 결과: {result}")
            return True
        except Exception as e:
            print(f"❌ {self.SCENARIO_NAME} 실패: {e}")
            return False


class CareerMTIGoalSettingTestScenario(BaseTest):
    """Career MTI Goal Setting 페이지 테스트."""

    SCENARIO_NAME = "자동검증 5: Career MTI Goal Setting"
    SCREENSHOT_FILENAME = "screenshot_career_mti_goal_setting.png"
    PAGE_PATH = "/mti/goal-setting/goal-state"

    async def run(self) -> bool:
        print(f"🚀 {self.SCENARIO_NAME} 시작")
        try:
            if not await self.mysuni_page.goto_page(self.PAGE_PATH):
                return False
            await self.mysuni_page.wait_for_page_loaded()
            screenshot_path = await self.take_screenshot(self.SCREENSHOT_FILENAME)
            result, llm_response = await self.validate_with_llm(
                screenshot_path, validation_mode="strict"
            )
            if result == "비정상":
                self.notify_failure(self.SCENARIO_NAME, llm_response, screenshot_path)
                return False
            print(f"✅ {self.SCENARIO_NAME} 완료 - 결과: {result}")
            return True
        except Exception as e:
            print(f"❌ {self.SCENARIO_NAME} 실패: {e}")
            return False


class CareerMTIInternalViewTestScenario(BaseTest):
    """Career MTI Internal View 페이지 테스트."""

    SCENARIO_NAME = "자동검증 5: Career MTI Internal View"
    SCREENSHOT_FILENAME = "screenshot_career_mti_internal_view.png"
    PAGE_PATH = "/mti/internal"

    async def run(self) -> bool:
        print(f"🚀 {self.SCENARIO_NAME} 시작")
        try:
            if not await self.mysuni_page.goto_page(self.PAGE_PATH):
                return False
            await self.mysuni_page.wait_for_page_loaded()
            screenshot_path = await self.take_screenshot(self.SCREENSHOT_FILENAME)
            result, llm_response = await self.validate_with_llm(
                screenshot_path, validation_mode="strict"
            )
            if result == "비정상":
                self.notify_failure(self.SCENARIO_NAME, llm_response, screenshot_path)
                return False
            print(f"✅ {self.SCENARIO_NAME} 완료 - 결과: {result}")
            return True
        except Exception as e:
            print(f"❌ {self.SCENARIO_NAME} 실패: {e}")
            return False
