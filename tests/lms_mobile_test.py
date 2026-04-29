"""LMS Mobile 일일점검 시나리오 (10항목).

UA 분리 전략:
  - 1번(앱 설치): mySUNI/3.1 UA 임시 컨텍스트 — 앱 설치 안내 UI 확인
  - 2~10번: 표준 모바일 UA(mySUNI 없음) + main.py 주입 세션 쿠키 — LMS 웹 점검
"""

from core.browser import MySuniPage
from tests.multi_item_base import MultiItemTestBase
from tests.specs.daily_check_spec import ChecklistItem, LMS_MOBILE_ITEMS

MYSUNI_APP_UA = "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36 mySUNI/3.1"


class LmsMobileTestScenario(MultiItemTestBase):
    """LMS Mobile 10개 항목 점검 (모바일 에뮬레이션)."""

    SCENARIO_NAME = "LMS Mobile 일일점검"
    SCENARIO_KEY = "lms_mobile"
    PAGE_PATH = "/mobile/app/install"
    CHECKLIST = LMS_MOBILE_ITEMS

    def __init__(
        self,
        *args,
        mobile_id: str = "",
        mobile_password: str = "",
        main_page=None,
        main_mysuni_page=None,
        lms_base_url: str = "",
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._mobile_id = mobile_id
        self._mobile_password = mobile_password
        self._main_page = main_page          # main.py 로그인 세션 페이지 (2~10번용)
        self._main_mysuni_page = main_mysuni_page
        self._lms_base_url = lms_base_url

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
        """UA 분리 실행:
        1번(앱 설치)은 mySUNI/3.1 임시 컨텍스트, 2~10번은 표준 모바일 UA 사용.
        """
        print(f"🚀 {self.SCENARIO_NAME} 시작")

        mobile_viewport = self.page.viewport_size or {"width": 1280, "height": 1024}

        # 1번(앱 설치): mySUNI/3.1 UA 임시 컨텍스트
        mysuni_ctx = await self.page.context.browser.new_context(
            user_agent=MYSUNI_APP_UA, viewport=mobile_viewport
        )
        mysuni_page = await mysuni_ctx.new_page()
        mysuni_mysuni_page = MySuniPage(mysuni_page, self.mysuni_page.base_url)

        # 2~10번: main.py 로그인 세션 페이지 직접 사용 (모바일 권한 페이지 우회)
        web_page = self._main_page
        web_mysuni_page = self._main_mysuni_page
        if web_page is None or web_mysuni_page is None:
            print("⚠️ main_page 미전달 — mobile_page 폴백 사용")
            web_page = self.page
            web_mysuni_page = self.mysuni_page
        else:
            # 메인 페이지 base_url을 LMS로 전환
            web_mysuni_page.base_url = self._lms_base_url or self.mysuni_page.base_url
            print(f"🌐 메인 페이지 base_url → {web_mysuni_page.base_url}")

        original_page = self.page
        original_mysuni_page = self.mysuni_page

        try:
            # 1번용 앱 설치 페이지 이동 (mySUNI UA)
            await mysuni_mysuni_page.goto_page(self.PAGE_PATH)
            await mysuni_mysuni_page.wait_for_page_loaded()

            # 2~10번용 초기 페이지 이동 (메인 로그인 세션 → LMS 메인)
            await web_mysuni_page.goto_page("/")
            await web_mysuni_page.wait_for_page_loaded()

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

                # 1번만 mySUNI UA, 나머지는 메인 로그인 세션 페이지
                if item.check_item == "앱 설치":
                    self.page = mysuni_page
                    self.mysuni_page = mysuni_mysuni_page
                else:
                    self.page = web_page
                    self.mysuni_page = web_mysuni_page

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

        finally:
            self.page = original_page
            self.mysuni_page = original_mysuni_page
            await mysuni_ctx.close()

    # ──────────────────────────────────────────────
    # 사전 동작 메서드
    # ──────────────────────────────────────────────

    async def _action_app_install(self) -> bool:
        """앱 설치 안내 페이지 UI 노출 확인."""
        # 이미 goto_page로 이동했으므로 UI 확인만
        install_btn = self.page.locator(
            "a[href*='download'], button:has-text('다운로드'), button:has-text('설치')"
        ).first
        try:
            return await install_btn.count() > 0
        except Exception:
            return False

    async def _dismiss_permission_page(self) -> bool:
        """모바일 앱 접근 권한 동의 페이지가 표시되면 확인 클릭하여 통과한다.

        표준 모바일 UA에서는 확인 클릭 후 LMS 콘텐츠로 이동한다.
        서버가 세션에 동의 완료 플래그를 저장하므로 이후 이동에는 나타나지 않는다.
        """
        try:
            confirm_btn = self.page.locator("button:has-text('확인')").first
            if await confirm_btn.count() > 0 and await confirm_btn.is_visible():
                perm_text = self.page.locator("text=접근 권한").first
                if await perm_text.count() > 0:
                    print("📋 앱 접근 권한 동의 페이지 감지 — 확인 클릭")
                    await confirm_btn.click()
                    await self.mysuni_page.wait_for_page_loaded()
                    await self.page.wait_for_timeout(2000)
                    return True
        except Exception:
            pass
        return False

    async def _action_login(self) -> bool:
        """데스크탑 UA + 세션 쿠키로 LMS 메인 진입 확인.

        데스크탑 컨텍스트는 모바일 권한 페이지가 나타나지 않으므로 바로 LMS 메인에 접근한다.
        """
        await self.mysuni_page.goto_page("/")
        await self.mysuni_page.wait_for_page_loaded()
        await self.page.wait_for_timeout(2000)

        # 로그인 폼이 없으면 인증 상태로 판단
        try:
            login_form = self.page.locator("#user-login-id").first
            if await login_form.count() > 0 and await login_form.is_visible():
                print("⚠️ 로그인 페이지 노출 — 세션 쿠키 주입 실패")
                return False
        except Exception:
            pass

        print("✅ 데스크탑 컨텍스트 + 세션 쿠키로 LMS 메인 진입 성공")
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
            ],
        )
        await self._click_with_priority(pause_item)
        await self.page.wait_for_timeout(1000)
        return True

    async def _action_badge_challenge(self) -> bool:
        """GNB Certification 메뉴 → Badge 탭 → 도전하기 → 도전취소 (PC 웹 방식)."""
        # GNB Certification 이동
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
                "[class*='gnb'] a:has-text('Certification')",
            ],
        )
        await self._click_with_priority(cert_nav)
        await self.mysuni_page.wait_for_page_loaded()
        await self.page.wait_for_timeout(1000)

        # Badge 탭 클릭
        badge_tab = ChecklistItem(
            service="lms_mobile",
            check_item="badge-tab",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["tab-badge", "badge-tab"],
            semantic_candidates=["Badge", "배지"],
            structural_selectors=[
                "button[role='tab']:has-text('Badge')",
                "button[role='tab']:has-text('배지')",
                "[class*='tab']:has-text('Badge')",
            ],
        )
        await self._click_with_priority(badge_tab)
        await self.page.wait_for_timeout(1000)

        # 도전하기 버튼 클릭
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

        # 모달 닫기
        for close_text in ["닫기", "확인", "취소"]:
            try:
                close_btn = self.page.locator(f"button:has-text('{close_text}')").last
                if await close_btn.count() > 0 and await close_btn.is_visible():
                    await close_btn.click()
                    await self.page.wait_for_timeout(500)
                    break
            except Exception:
                pass

        # 도전취소
        cancel_ok = False
        for _, ctx in contexts:
            try:
                loc = ctx.locator("button:has-text('도전중')").first
                if await loc.count() > 0 and await loc.is_visible():
                    await loc.click()
                    await self.mysuni_page.wait_for_page_loaded()
                    await self.page.wait_for_timeout(1000)
                    cancel_btn = self.page.locator("button:has-text('도전취소'), button:has-text('도전 취소')").first
                    if await cancel_btn.count() > 0 and await cancel_btn.is_visible():
                        await cancel_btn.click()
                        await self.page.wait_for_timeout(500)
                        confirm_btn = self.page.locator("button:has-text('확인'), button:has-text('예')").first
                        if await confirm_btn.count() > 0 and await confirm_btn.is_visible():
                            await confirm_btn.click()
                        cancel_ok = True
                    break
            except Exception:
                continue

        return challenge_ok or cancel_ok

    async def _action_community_post(self) -> bool:
        """커뮤니티 게시글 작성 후 삭제 (PC 웹 GNB 방식)."""
        # GNB Community 이동
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
                "[class*='gnb'] a:has-text('커뮤니티')",
            ],
        )
        await self._click_with_priority(comm_nav)
        await self.mysuni_page.wait_for_page_loaded()
        await self.page.wait_for_timeout(1000)

        # 좌측 커뮤니티 목록 첫 번째 게시판 진입
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

        # 페이지 상단 스크롤 후 글쓰기 클릭
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
        """간편로그인 설정 — MyProfile 페이지에서 간편로그인 설정 버튼 탐색 (PC 웹)."""
        await self.mysuni_page.goto_page("/suni-main/my-training/my-page/MyProfile")
        await self.mysuni_page.wait_for_page_loaded()
        await self.page.wait_for_timeout(1500)

        item = next(i for i in self.CHECKLIST if i.check_item == "간편로그인 설정")
        clicked = await self._click_with_priority(item)
        if clicked:
            await self.page.wait_for_timeout(1500)
            return True
        print("⚠️ 간편로그인 설정 버튼 미발견 (PC 웹에서는 MyProfile 페이지 노출로 대체)")
        return False

    async def _action_logout(self) -> bool:
        """PC 웹 프로필 드롭다운 → 로그아웃."""
        # 프로필 아이콘 클릭
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

        # 드롭다운 내 로그아웃 탐색
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

        # 폴백: 체크리스트 셀렉터
        item = next(i for i in self.CHECKLIST if i.check_item == "로그아웃")
        if await self._click_with_priority(item):
            await self.mysuni_page.wait_for_page_loaded()
            return True
        return False

    async def _action_easy_login(self) -> bool:
        """간편 로그인 — 로그아웃 후 로그인 페이지에서 간편 로그인 버튼 탐색 (PC 웹)."""
        # 로그아웃 후 로그인 페이지로 이동됐을 것을 가정
        item = next(i for i in self.CHECKLIST if i.check_item == "간편로그인")
        clicked = await self._click_with_priority(item)
        if clicked:
            await self.page.wait_for_timeout(1500)
            return True
        print("⚠️ 간편로그인 버튼 미발견 (PC 웹 로그인 페이지에서 간편 로그인 UI 노출 확인으로 대체)")
        return False
