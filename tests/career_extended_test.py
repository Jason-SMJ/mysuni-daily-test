"""Career 확장 점검 시나리오 (7항목: Career추천 + My Pick).

기존 career_profile_test.py(10항목)를 유지하면서
Career추천·My Pick 관련 신규 7개 항목을 별도 시나리오로 운영한다.
"""

from tests.multi_item_base import MultiItemTestBase
from tests.specs.daily_check_spec import ChecklistItem, CAREER_EXTENDED_ITEMS


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

    # ──────────────────────────────────────────────
    # 사전 동작 메서드
    # ──────────────────────────────────────────────

    async def _action_navigate_recommend(self) -> bool:
        """Career 추천 메뉴 이동."""
        item = next(i for i in self.CHECKLIST if i.check_item == "Career 추천 이동")
        clicked = await self._click_with_priority(item)
        if clicked:
            await self.mysuni_page.wait_for_page_loaded()
            return True
        # 클릭 실패 시 직접 이동
        return await self.mysuni_page.goto_page("/career/recommend")

    async def _action_preview_job(self) -> bool:
        """추천 직무 항목 클릭하여 미리보기 화면 진입."""
        item = next(i for i in self.CHECKLIST if i.check_item == "Career 추천 직무 미리보기")
        clicked = await self._click_with_priority(item)
        if clicked:
            await self.mysuni_page.wait_for_page_loaded()
            await self.page.wait_for_timeout(1000)
            # 뒤로가기 (미리보기 → 추천 목록)
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

        # 검색창이 없으면 더보기 버튼 클릭으로 탐색 확인
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
