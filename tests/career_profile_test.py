"""Career Profile 일일점검 체크리스트 기반 파일럿 시나리오."""

from tests.multi_item_base import MultiItemTestBase, ActionOutcome
from tests.specs.daily_check_spec import ChecklistItem, CAREER_PROFILE_ITEMS


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

    # ──────────────────────────────────────────────
    # Career-specific 사전 동작 메서드
    # ──────────────────────────────────────────────

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
