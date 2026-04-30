"""LMS Mobile 일일점검 시나리오 (10항목).

모든 항목에 동일한 Android + mySUNI/3.1 UA 사용.
UA: Mozilla/5.0 (Linux; Android 13; ...) Chrome/116.0.0.0 Mobile Safari/537.36 mySUNI/3.1
진입 URL: https://mysuni.sk.com/suni-mobile/
"""

from tests.multi_item_base import MultiItemTestBase
from tests.specs.daily_check_spec import ChecklistItem, LMS_MOBILE_ITEMS

ANDROID_MYSUNI_UA = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/116.0.0.0 Mobile Safari/537.36 mySUNI/3.1"
)
SUNI_MOBILE_PATH = "/suni-mobile/"


class LmsMobileTestScenario(MultiItemTestBase):
    """LMS Mobile 10개 항목 점검 (Android + mySUNI/3.1 UA 단일 컨텍스트)."""

    SCENARIO_NAME = "LMS Mobile 일일점검"
    SCENARIO_KEY = "lms_mobile"
    PAGE_PATH = "/mobile/app/install"
    CHECKLIST = LMS_MOBILE_ITEMS

    def __init__(self, *args, mobile_id: str = "", mobile_password: str = "", **kwargs):
        # 구형 파라미터 호환성 유지
        kwargs.pop("main_page", None)
        kwargs.pop("main_mysuni_page", None)
        kwargs.pop("lms_base_url", None)
        super().__init__(*args, **kwargs)
        self._mobile_id = mobile_id
        self._mobile_password = mobile_password

    def _build_action_map(self):
        return {
            "앱 설치": self._action_app_install,
            "로그인": self._action_login,
            "카드 확인": self._action_select_card,
            "큐브 확인": self._action_select_cube,
            "영상 확인": self._action_play_video,
            "배지 확인": self._action_badge_challenge,
            "커뮤니티 확인": self._action_community_post,
            "간편로그인 설정": self._action_easy_login_setup,
            "로그아웃": self._action_logout,
            "간편로그인": self._action_easy_login,
        }

    async def run(self) -> bool:
        """단일 Android + mySUNI/3.1 UA 컨텍스트로 10개 항목 순차 점검."""
        print(f"🚀 {self.SCENARIO_NAME} 시작")
        print(f"🤖 UA: {ANDROID_MYSUNI_UA}")

        try:
            # 앱 설치 페이지로 초기 이동 (1번 준비)
            if not await self.mysuni_page.goto_page(self.PAGE_PATH):
                return False
            await self.mysuni_page.wait_for_page_loaded()

            action_map = self._build_action_map()
            indexed_items = list(enumerate(self.CHECKLIST, start=1))

            if self.target_item_index is not None:
                indexed_items = [
                    (idx, item)
                    for idx, item in indexed_items
                    if idx == self.target_item_index
                ]
                if not indexed_items:
                    print(f"❌ 잘못된 item 인덱스: {self.target_item_index}")
                    return False

            failed_items: list[str] = []
            for order, (idx, item) in enumerate(indexed_items, start=1):
                print(f"\n[{order}/{len(indexed_items)}] {item.check_item}")
                ok, _ = await self._run_item(idx, item, action_map.get(item.check_item))
                await self._post_item_hook(item)
                if item.action_type == "popup":
                    await self._close_all_popups(item)
                if not ok:
                    failed_items.append(item.check_item)

            if failed_items:
                print(f"❌ {self.SCENARIO_NAME} 실패 항목: {', '.join(failed_items)}")
                return False

            print(f"✅ {self.SCENARIO_NAME} 완료")
            return True

        except Exception as e:
            print(f"❌ {self.SCENARIO_NAME} 실패: {e}")
            return False

    # ──────────────────────────────────────────────
    # 공통 유틸
    # ──────────────────────────────────────────────

    async def _handle_aos_access_auth(self) -> bool:
        """sso/aos-access-auth 권한 동의 페이지 감지 시 확인 클릭."""
        if "aos-access-auth" in self.page.url or "sso" in self.page.url:
            confirm_btn = self.page.locator("button:has-text('확인')").first
            try:
                if await confirm_btn.count() > 0 and await confirm_btn.is_visible():
                    print("📋 AOS 접근 권한 동의 페이지 감지 — 확인 클릭")
                    await confirm_btn.click()
                    await self.mysuni_page.wait_for_page_loaded()
                    await self.page.wait_for_timeout(2000)
                    return True
            except Exception:
                pass
        return False

    # ──────────────────────────────────────────────
    # 사전 동작 메서드
    # ──────────────────────────────────────────────

    async def _action_app_install(self) -> bool:
        """앱 설치 안내 페이지 UI 노출 확인."""
        install_btn = self.page.locator(
            "a[href*='download'], button:has-text('앱 다운로드'), button:has-text('다운로드')"
        ).first
        try:
            return await install_btn.count() > 0
        except Exception:
            return False

    async def _action_login(self) -> bool:
        """/suni-mobile/ 진입 → AOS 권한 동의 → SSO 세션 인증 완료 대기 → LMS 도달 확인."""
        await self.mysuni_page.goto_page(SUNI_MOBILE_PATH)
        await self.mysuni_page.wait_for_page_loaded()
        await self.page.wait_for_timeout(2000)

        # AOS 접근 권한 동의 처리
        await self._handle_aos_access_auth()

        # SSO 세션 인증 리다이렉트 완료 대기 (sid-auth → LMS)
        for _ in range(15):
            url = self.page.url
            if "sid-auth.mysuni.com" in url or "about:blank" in url:
                print(f"⏳ SSO 리다이렉트 대기 중... ({url[:60]})")
                await self.page.wait_for_timeout(2000)
            else:
                break

        await self.page.wait_for_timeout(2000)
        final_url = self.page.url
        print(f"✅ 최종 URL: {final_url}")

        # 로그인 폼이 없으면 인증 상태로 판단
        try:
            login_form = self.page.locator("#user-login-id").first
            if await login_form.count() > 0 and await login_form.is_visible():
                print("⚠️ 로그인 페이지 노출 — 인증 실패")
                return False
        except Exception:
            pass

        return True

    async def _action_select_card(self) -> bool:
        """마이홀 페이지 카드 클릭."""
        item = next(i for i in self.CHECKLIST if i.check_item == "카드 확인")
        if await self._click_with_priority(item):
            await self.mysuni_page.wait_for_page_loaded()
            return True
        return False

    async def _action_select_cube(self) -> bool:
        """카드 상세에서 Video 큐브 클릭."""
        item = next(i for i in self.CHECKLIST if i.check_item == "큐브 확인")
        if await self._click_with_priority(item):
            await self.mysuni_page.wait_for_page_loaded()
            return True
        return False

    async def _action_play_video(self) -> bool:
        """재생 후 중단."""
        item = next(i for i in self.CHECKLIST if i.check_item == "영상 확인")
        if not await self._click_with_priority(item):
            return False
        await self.page.wait_for_timeout(3000)

        pause_item = ChecklistItem(
            service="lms_mobile",
            check_item="영상-중단",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["player-pause", "btn-pause"],
            semantic_candidates=["중단", "일시정지", "Pause"],
            structural_selectors=[
                "button[aria-label*='중단']",
                "button[aria-label*='pause' i]",
                "[class*='pause-icon']",
            ],
        )
        await self._click_with_priority(pause_item)
        await self.page.wait_for_timeout(1000)
        return True

    async def _action_badge_challenge(self) -> bool:
        """GNB Certification → Badge 탭 → 도전하기 → 도전취소."""
        cert_nav = ChecklistItem(
            service="lms_mobile",
            check_item="cert-nav",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["menu-certification", "nav-certification"],
            semantic_candidates=["Certification", "자격증", "배지"],
            structural_selectors=[
                "a[href*='certification']",
                "nav a:has-text('Certification')",
            ],
        )
        await self._click_with_priority(cert_nav)
        await self.mysuni_page.wait_for_page_loaded()
        await self.page.wait_for_timeout(1000)

        badge_tab = ChecklistItem(
            service="lms_mobile",
            check_item="badge-tab",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["tab-badge"],
            semantic_candidates=["Badge", "배지"],
            structural_selectors=[
                "button[role='tab']:has-text('Badge')",
                "[class*='tab']:has-text('Badge')",
            ],
        )
        await self._click_with_priority(badge_tab)
        await self.page.wait_for_timeout(1000)

        challenge_ok = False
        contexts = await self._iter_contexts()
        for _, ctx in contexts:
            for selector in ["button:has-text('도전하기')", "[class*='badge'] button:has-text('도전')"]:
                try:
                    loc = ctx.locator(selector).first
                    if await loc.count() > 0 and await loc.is_visible():
                        await loc.click()
                        await self.page.wait_for_timeout(1500)
                        challenge_ok = True
                        break
                except Exception:
                    continue
            if challenge_ok:
                break

        for close_text in ["닫기", "확인", "취소"]:
            try:
                close_btn = self.page.locator(f"button:has-text('{close_text}')").last
                if await close_btn.count() > 0 and await close_btn.is_visible():
                    await close_btn.click()
                    await self.page.wait_for_timeout(500)
                    break
            except Exception:
                pass

        cancel_ok = False
        for _, ctx in contexts:
            try:
                loc = ctx.locator("button:has-text('도전중')").first
                if await loc.count() > 0 and await loc.is_visible():
                    await loc.click()
                    await self.mysuni_page.wait_for_page_loaded()
                    await self.page.wait_for_timeout(1000)
                    cancel_btn = self.page.locator(
                        "button:has-text('도전취소'), button:has-text('도전 취소')"
                    ).first
                    if await cancel_btn.count() > 0 and await cancel_btn.is_visible():
                        await cancel_btn.click()
                        await self.page.wait_for_timeout(500)
                        confirm_btn = self.page.locator(
                            "button:has-text('확인'), button:has-text('예')"
                        ).first
                        if await confirm_btn.count() > 0 and await confirm_btn.is_visible():
                            await confirm_btn.click()
                        cancel_ok = True
                    break
            except Exception:
                continue

        return challenge_ok or cancel_ok

    async def _action_community_post(self) -> bool:
        """커뮤니티 게시글 작성 후 삭제."""
        comm_nav = ChecklistItem(
            service="lms_mobile",
            check_item="community-nav",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["menu-community", "nav-community"],
            semantic_candidates=["Community", "커뮤니티"],
            structural_selectors=[
                "a[href*='community']",
                "nav a:has-text('Community')",
            ],
        )
        await self._click_with_priority(comm_nav)
        await self.mysuni_page.wait_for_page_loaded()
        await self.page.wait_for_timeout(1000)

        board_item = ChecklistItem(
            service="lms_mobile",
            check_item="community-board",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=[],
            semantic_candidates=[],
            structural_selectors=[
                "[class*='my-community'] li:first-child",
                "aside li:first-child a",
                "[class*='community'] li:first-child a",
            ],
        )
        await self._click_with_priority(board_item)
        await self.page.wait_for_timeout(1000)
        await self.page.evaluate("window.scrollTo(0, 0)")
        await self.page.wait_for_timeout(300)

        item = next(i for i in self.CHECKLIST if i.check_item == "커뮤니티 확인")
        write_item = ChecklistItem(
            service="lms_mobile",
            check_item="community-write",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["btn-write-post", "community-write"],
            semantic_candidates=["글쓰기", "작성", "새 글"],
            structural_selectors=[
                "button:has-text('글쓰기')",
                "button:has-text('작성')",
                "a:has-text('글쓰기')",
                "[class*='write'] button",
                "a[href*='/write']",
            ],
        )
        if not await self._click_with_priority(write_item):
            if not await self._click_with_priority(item):
                return False
        await self.page.wait_for_timeout(1500)

        title_input = self.page.locator("input[placeholder*='제목']").first
        content_input = self.page.locator("textarea, [contenteditable='true']").first
        try:
            if await title_input.count() > 0:
                await title_input.fill("[자동점검] Mobile 커뮤니티 테스트")
            if await content_input.count() > 0:
                await content_input.fill("자동 점검 게시글. 확인 후 삭제됩니다.")
        except Exception:
            pass

        submit_item = ChecklistItem(
            service="lms_mobile",
            check_item="post-submit",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["btn-submit"],
            semantic_candidates=["등록", "게시"],
            structural_selectors=["button:has-text('등록')", "button[type='submit']"],
        )
        if not await self._click_with_priority(submit_item):
            return False
        await self.mysuni_page.wait_for_page_loaded()
        await self.page.wait_for_timeout(1500)

        post_link = self.page.get_by_text("[자동점검] Mobile 커뮤니티 테스트").first
        try:
            if await post_link.count() > 0:
                await post_link.click()
                await self.mysuni_page.wait_for_page_loaded()
                await self.page.wait_for_timeout(1000)
        except Exception:
            pass

        delete_item = ChecklistItem(
            service="lms_mobile",
            check_item="post-delete",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["btn-delete"],
            semantic_candidates=["삭제"],
            structural_selectors=["button:has-text('삭제')"],
        )
        await self._click_with_priority(delete_item)
        await self.page.wait_for_timeout(500)
        confirm_item = ChecklistItem(
            service="lms_mobile",
            check_item="post-delete-confirm",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["btn-confirm"],
            semantic_candidates=["확인"],
            structural_selectors=["button:has-text('확인')"],
        )
        await self._click_with_priority(confirm_item)
        await self.mysuni_page.wait_for_page_loaded()
        return True

    async def _action_easy_login_setup(self) -> bool:
        """간편로그인 설정 — MyProfile 페이지 노출 (PC 웹 대체)."""
        await self.mysuni_page.goto_page("/suni-main/my-training/my-page/MyProfile")
        await self.mysuni_page.wait_for_page_loaded()
        await self.page.wait_for_timeout(1500)

        item = next(i for i in self.CHECKLIST if i.check_item == "간편로그인 설정")
        if await self._click_with_priority(item):
            await self.page.wait_for_timeout(1500)
            return True
        print("⚠️ 간편로그인 설정 버튼 미발견")
        return False

    async def _action_logout(self) -> bool:
        """프로필 드롭다운 → 로그아웃."""
        profile_item = ChecklistItem(
            service="lms_mobile",
            check_item="profile-menu",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["profile-icon", "user-avatar", "btn-profile"],
            semantic_candidates=["프로필", "Profile"],
            structural_selectors=[
                "button[aria-label*='프로필']",
                "[class*='profile'] button",
                "[class*='avatar']",
                "[class*='gnb'] [class*='user']",
                "[class*='header'] [class*='user']",
            ],
        )
        await self._click_with_priority(profile_item)
        await self.page.wait_for_timeout(1000)

        contexts = await self._iter_contexts()
        for _, ctx in contexts:
            for selector in [
                "[class*='lg-out']",
                "a[class*='lg-out']",
                "a[class*='logout']",
                "li:has-text('로그아웃') a",
                "a:has-text('로그아웃')",
                "button:has-text('로그아웃')",
            ]:
                try:
                    loc = ctx.locator(selector).first
                    if await loc.count() > 0 and await loc.is_visible():
                        await loc.click()
                        await self.mysuni_page.wait_for_page_loaded()
                        return True
                except Exception:
                    continue

        item = next(i for i in self.CHECKLIST if i.check_item == "로그아웃")
        if await self._click_with_priority(item):
            await self.mysuni_page.wait_for_page_loaded()
            return True
        return False

    async def _action_easy_login(self) -> bool:
        """로그인 페이지에서 간편 로그인 버튼 탐색."""
        item = next(i for i in self.CHECKLIST if i.check_item == "간편로그인")
        if await self._click_with_priority(item):
            await self.page.wait_for_timeout(1500)
            return True
        print("⚠️ 간편로그인 버튼 미발견")
        return False
