"""One_ID 일일점검 시나리오 (5항목: 일반사용자 화면).

관리자 VDI 화면(6~10번)은 자동화 범위 외로 제외.
- 1~4번: 신규 브라우저 컨텍스트(세션 없음)로 SSO 로그인 페이지 직접 진입
- 5번: main.py 로그인 세션이 있는 원본 컨텍스트로 MyProfile 진입
"""

from core.browser import MySuniPage
from tests.multi_item_base import MultiItemTestBase
from tests.specs.daily_check_spec import ChecklistItem, ONE_ID_ITEMS

SSO_LOGIN_URL = "https://sid-auth.mysuni.com/login"


class OneIdTestScenario(MultiItemTestBase):
    """One_ID 통합 로그인 5개 항목 점검."""

    SCENARIO_NAME = "One_ID 일일점검 (일반사용자)"
    SCENARIO_KEY = "one_id"
    PAGE_PATH = "/"
    CHECKLIST = ONE_ID_ITEMS

    def __init__(self, *args, user_id: str = "", user_password: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._user_id = user_id
        self._user_password = user_password

    def _build_action_map(self):
        return {
            "로그인 페이지": self._action_login_page,
            "로그인": self._action_login,
            "ID 찾기": self._action_find_id,
            "개인정보처리방침": self._action_privacy_policy,
            "내정보": self._action_my_info,
        }

    async def run(self) -> bool:
        """1~4번은 신규 컨텍스트, 5번은 원본 컨텍스트로 실행."""
        print(f"🚀 {self.SCENARIO_NAME} 시작")

        viewport = self.page.viewport_size or {"width": 1280, "height": 1024}
        fresh_context = await self.page.context.browser.new_context(viewport=viewport)
        fresh_page = await fresh_context.new_page()
        fresh_mysuni_page = MySuniPage(fresh_page, self.mysuni_page.base_url)

        original_page = self.page
        original_mysuni_page = self.mysuni_page

        try:
            action_map = self._build_action_map()
            indexed_items = list(enumerate(self.CHECKLIST, start=1))
            failed_items: list[str] = []

            # 신규 컨텍스트(세션 없음)로 실행할 항목
            FRESH_CONTEXT_ITEMS = {"로그인 페이지", "로그인", "ID 찾기"}

            for order, (idx, item) in enumerate(indexed_items, start=1):
                print(f"\n[{order}/{len(indexed_items)}] {item.check_item}")

                # 1~3번: 신규 컨텍스트(세션 없음) / 4~5번: 원본 페이지(로그인 세션)
                if item.check_item in FRESH_CONTEXT_ITEMS:
                    self.page = fresh_page
                    self.mysuni_page = fresh_mysuni_page
                else:
                    self.page = original_page
                    self.mysuni_page = original_mysuni_page

                ok, _ = await self._run_item(idx, item, action_map.get(item.check_item))
                await self._post_item_hook(item)
                if item.action_type == "popup":
                    await self._close_all_popups(item)
                if not ok:
                    failed_items.append(item.check_item)

            if failed_items:
                print(f"❌ {self.SCENARIO_NAME} 실패 항목: {', '.join(failed_items)}")
                return False

            print(f"✅ {self.SCENARIO_NAME} 완료 - {len(indexed_items)}개 항목 통과")
            return True

        except Exception as e:
            print(f"❌ {self.SCENARIO_NAME} 실패: {e}")
            return False

        finally:
            self.page = original_page
            self.mysuni_page = original_mysuni_page
            await fresh_context.close()

    async def _goto_sso_login(self) -> None:
        """mysuni.sk.com 진입 → SSO OAuth 리다이렉트로 로그인 페이지 도달.

        sid-auth.mysuni.com/login 직접 호출 시 OAuth 파라미터 누락으로 403이 발생하므로
        반드시 mysuni.sk.com/ 경유로 진입해야 한다.
        """
        await self.page.goto(self.mysuni_page.base_url, wait_until="networkidle")
        await self.page.wait_for_timeout(1500)

    # ──────────────────────────────────────────────
    # 사전 동작 메서드
    # ──────────────────────────────────────────────

    async def _action_login_page(self) -> bool:
        """신규 컨텍스트에서 SSO 로그인 URL 직접 접속 — ID/PWD 입력창 확인."""
        await self._goto_sso_login()
        id_input = self.page.locator(
            "#user-login-id, input[name='userId'], input[type='text'][placeholder*='ID']"
        ).first
        try:
            return await id_input.count() > 0 and await id_input.is_visible()
        except Exception:
            return False

    async def _action_login(self) -> bool:
        """ID/PW 직접 입력 후 로그인 버튼 클릭 (신규 컨텍스트)."""
        try:
            await self.page.wait_for_selector("#user-login-id", timeout=8000)
            await self.page.fill("#user-login-id", self._user_id)
            await self.page.fill("#user-password", self._user_password)
            await self.page.get_by_role("button", name="로그인").click()
            await self.mysuni_page.wait_for_page_loaded()
            await self.page.wait_for_timeout(2000)
            return True
        except Exception as e:
            print(f"⚠️ one_id 로그인 폼 입력 실패: {e}")
            return False

    async def _action_find_id(self) -> bool:
        """신규 컨텍스트 세션 전체 초기화 후 SSO 로그인 페이지에서 ID 찾기 탭 진입."""
        # 2번 로그인 후 세션이 생겼을 수 있으므로 쿠키·스토리지 전체 초기화
        await self.page.context.clear_cookies()
        try:
            await self.page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
        except Exception:
            pass
        await self._goto_sso_login()

        item = next(i for i in self.CHECKLIST if i.check_item == "ID 찾기")
        clicked = await self._click_with_priority(item)
        if clicked:
            await self.page.wait_for_timeout(1500)
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
        """LMS 메인 하단 푸터의 개인정보처리방침 클릭 (원본 로그인 세션 사용)."""
        await self.mysuni_page.goto_page("/")
        await self.mysuni_page.wait_for_page_loaded()
        await self.page.wait_for_timeout(1000)

        # 페이지 맨 아래로 스크롤하여 푸터 링크 노출
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await self.page.wait_for_timeout(500)

        item = next(i for i in self.CHECKLIST if i.check_item == "개인정보처리방침")
        clicked = await self._click_with_priority(item)
        if clicked:
            await self.mysuni_page.wait_for_page_loaded()
            await self.page.wait_for_timeout(1000)
            await self.page.go_back()
            await self.mysuni_page.wait_for_page_loaded()
            return True
        return False

    async def _action_my_info(self) -> bool:
        """원본 컨텍스트(로그인 세션)로 MyProfile 접속 후 두 번째 '정보 설정' 버튼 클릭."""
        if not await self.mysuni_page.goto_page(
            "/suni-main/my-training/my-page/MyProfile"
        ):
            return False
        await self.mysuni_page.wait_for_page_loaded()
        await self.page.wait_for_timeout(2000)

        contexts = await self._iter_contexts()
        for _, ctx in contexts:
            for selector in [
                "button:has-text('정보 설정')",
                "a:has-text('정보 설정')",
                "button:has-text('정보설정')",
                "a:has-text('정보설정')",
            ]:
                try:
                    loc = ctx.locator(selector)
                    count = await loc.count()
                    target = loc.nth(1) if count >= 2 else loc.first
                    if await target.count() > 0 and await target.is_visible():
                        await target.scroll_into_view_if_needed()
                        await target.click()
                        await self.mysuni_page.wait_for_page_loaded()
                        await self.page.wait_for_timeout(1500)
                        return True
                except Exception:
                    continue
        return False
