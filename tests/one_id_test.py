"""One_ID 일일점검 시나리오 (5항목: 일반사용자 화면).

관리자 VDI 화면(6~10번)은 자동화 범위 외로 제외.
base_url은 mysuni.sk.com (LMS)을 사용한다.
"""

from tests.multi_item_base import MultiItemTestBase
from tests.specs.daily_check_spec import ChecklistItem, ONE_ID_ITEMS


class OneIdTestScenario(MultiItemTestBase):
    """One_ID 통합 로그인 5개 항목 점검."""

    SCENARIO_NAME = "One_ID 일일점검 (일반사용자)"
    SCENARIO_KEY = "one_id"
    PAGE_PATH = "/"
    CHECKLIST = ONE_ID_ITEMS

    def _build_action_map(self):
        return {
            "로그인 페이지": self._action_login_page,
            "로그인": self._action_login,
            "ID 찾기": self._action_find_id,
            "개인정보처리방침": self._action_privacy_policy,
            "내정보": self._action_my_info,
        }

    # ──────────────────────────────────────────────
    # 사전 동작 메서드
    # ──────────────────────────────────────────────

    async def _action_login_page(self) -> bool:
        """통합ID 로그인 페이지 접속 및 UI 확인."""
        # 이미 PAGE_PATH로 이동했으므로 ID/PWD 입력창 존재 여부 확인
        id_input = self.page.locator(
            "#user-login-id, input[name='userId'], input[type='text'][placeholder*='ID']"
        ).first
        try:
            return await id_input.count() > 0 and await id_input.is_visible()
        except Exception:
            return False

    async def _action_login(self) -> bool:
        """ID, Password 입력 후 로그인."""
        item = next(i for i in self.CHECKLIST if i.check_item == "로그인")
        if await self._click_with_priority(item):
            await self.mysuni_page.wait_for_page_loaded()
            return True
        return False

    async def _action_find_id(self) -> bool:
        """로그인 페이지에서 ID 찾기 탭 진입."""
        # 로그인 페이지로 복귀
        if "mysuni" not in self.page.url or "lms" in self.page.url:
            await self.mysuni_page.goto_page("/")
            await self.mysuni_page.wait_for_page_loaded()

        item = next(i for i in self.CHECKLIST if i.check_item == "ID 찾기")
        clicked = await self._click_with_priority(item)
        if clicked:
            await self.page.wait_for_timeout(1500)
            # ID 찾기 탭 클릭
            find_tab = ChecklistItem(
                service="one_id",
                check_item="id-찾기-탭",
                check_detail="",
                expected_result="",
                mode="playwright",
                action_type="click",
                data_testids=["tab-find-id"],
                semantic_candidates=["ID찾기", "아이디 찾기"],
                structural_selectors=["button:has-text('ID찾기')", "a:has-text('ID찾기')"],
            )
            await self._click_with_priority(find_tab)
            await self.page.wait_for_timeout(1000)
            return True
        return False

    async def _action_privacy_policy(self) -> bool:
        """하단 개인정보처리방침 클릭."""
        # 로그인 페이지로 복귀
        await self.mysuni_page.goto_page("/")
        await self.mysuni_page.wait_for_page_loaded()

        item = next(i for i in self.CHECKLIST if i.check_item == "개인정보처리방침")
        clicked = await self._click_with_priority(item)
        if clicked:
            await self.mysuni_page.wait_for_page_loaded()
            await self.page.wait_for_timeout(1000)
            # 뒤로가기
            await self.page.go_back()
            await self.mysuni_page.wait_for_page_loaded()
            return True
        return False

    async def _action_my_info(self) -> bool:
        """LMS myPage 프로필 설정에서 내정보 버튼 클릭."""
        if not await self.mysuni_page.goto_page("/suni-main/mypage?page=/profile-setting"):
            return False
        await self.mysuni_page.wait_for_page_loaded()
        await self.page.wait_for_timeout(1500)

        item = next(i for i in self.CHECKLIST if i.check_item == "내정보")
        clicked = await self._click_with_priority(item)
        if clicked:
            await self.mysuni_page.wait_for_page_loaded()
            await self.page.wait_for_timeout(1000)
            return True
        return False
