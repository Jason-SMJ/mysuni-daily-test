"""LMS PC 일일점검 시나리오 (8항목)."""

from tests.multi_item_base import MultiItemTestBase
from tests.specs.daily_check_spec import ChecklistItem, LMS_PC_ITEMS


class LmsPcTestScenario(MultiItemTestBase):
    """LMS PC 8개 체크리스트 항목 순차 점검."""

    SCENARIO_NAME = "LMS PC 일일점검"
    SCENARIO_KEY = "lms_pc"
    PAGE_PATH = "/"
    CHECKLIST = LMS_PC_ITEMS

    def _build_action_map(self):
        return {
            "로그인": self._action_login,
            "카드 확인": self._action_select_card,
            "큐브 확인": self._action_select_cube,
            "영상 확인": self._action_play_video,
            "검색 확인": self._action_search,
            "배지 확인": self._action_badge_challenge,
            "커뮤니티 확인": self._action_community_post,
            "로그아웃": self._action_logout,
        }

    # ──────────────────────────────────────────────
    # 사전 동작 메서드
    # ──────────────────────────────────────────────

    async def _action_login(self) -> bool:
        """toktok SSO 시도 → 실패 시 직접 ID/PWD 로그인."""
        sso_item = ChecklistItem(
            service="lms_pc",
            check_item="toktok-sso",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["btn-sso-login", "toktok-login"],
            semantic_candidates=["toktok으로 로그인", "SSO 로그인"],
            structural_selectors=["a[href*='toktok']", "button:has-text('toktok')"],
        )
        sso_ok = await self._click_with_priority(sso_item)
        if sso_ok:
            await self.mysuni_page.wait_for_page_loaded()
            if self.mysuni_page.base_url in self.page.url or "mysuni" in self.page.url:
                return True

        # 직접 로그인 폼
        item = next(i for i in self.CHECKLIST if i.check_item == "로그인")
        if await self._click_with_priority(item):
            await self.mysuni_page.wait_for_page_loaded()
            return True
        return False

    async def _action_select_card(self) -> bool:
        """메인 카드 목록에서 첫 번째 카드 클릭."""
        item = next(i for i in self.CHECKLIST if i.check_item == "카드 확인")
        if await self._click_with_priority(item):
            await self.mysuni_page.wait_for_page_loaded()
            return True
        return False

    async def _action_select_cube(self) -> bool:
        """카드 상세 페이지 LNB에서 btn-state-cube 클래스 기반으로 Video 큐브 클릭."""
        item = next(i for i in self.CHECKLIST if i.check_item == "큐브 확인")

        # btn-state-cube 클래스 우선 탐색 (모든 프레임 포함)
        contexts = await self._iter_contexts()
        for _, ctx in contexts:
            for selector in [
                "[class*='btn-state-cube']",
                "button[class*='btn-state-cube']",
            ]:
                try:
                    loc = ctx.locator(selector).first
                    if await loc.count() > 0 and await loc.is_visible():
                        await loc.click()
                        await self.mysuni_page.wait_for_page_loaded()
                        await self.page.wait_for_timeout(1000)  # 큐브 화면 안정화 대기
                        return True
                except Exception:
                    continue

        # 폴백: 기존 4단계 클릭 전략
        if await self._click_with_priority(item):
            await self.mysuni_page.wait_for_page_loaded()
            await self.page.wait_for_timeout(1000)  # 큐브 화면 안정화 대기
            return True
        return False

    async def _action_play_video(self) -> bool:
        """재생 버튼 클릭 후 중단 버튼 클릭."""
        # 팝업 플레이어 로딩 대기 (증가: 3s → 5s)
        await self.page.wait_for_timeout(5000)

        # 재생 버튼 선택자 (player-icon 클래스 최우선)
        play_selectors = [
            # player-icon 클래스 기반 (판업토 플레이어)
            "[class*='player-icon']",
            "button[class*='player-icon']",
            # data-testid
            "[data-testid='player-play']",
            "[data-testid='btn-play']",
            "[data-testid='video-play-button']",
            # aria-label
            "button[aria-label*='재생']",
            "button[aria-label*='play' i]",
            "button[aria-label*='Play']",
            "button[title*='재생']",
            "button[title*='play' i]",
            # class 기반 폴백
            "button[class*='play']",
            "[class*='player'] button[class*='play']",
            "[class*='Player'] button",
            "[class*='vjs-play-control']",
            # 썸네일/영상 영역 오버레이 재생 버튼 (mySUNI panuto 플레이어)
            "[class*='thumbnail'] button",
            "[class*='thumb'] button",
            "[class*='video-wrap'] button",
            "[class*='videoWrap'] button",
            "[class*='video_wrap'] button",
            "[class*='cube-play']",
            "[class*='play-btn']",
            "[class*='playBtn']",
            # video 요소 직접 클릭
            "video",
        ]

        contexts = await self._iter_contexts()
        clicked = False
        for _, ctx in contexts:
            for selector in play_selectors:
                try:
                    loc = ctx.locator(selector).first
                    if await loc.count() > 0 and await loc.is_visible():
                        await loc.click()
                        clicked = True
                        break
                except Exception:
                    continue
            if clicked:
                break

        # JS 폴백: video 요소에 play() 직접 호출 (프레임 포함)
        if not clicked:
            for _, ctx in contexts:
                try:
                    played = await ctx.evaluate(
                        """() => {
                            const v = document.querySelector('video');
                            if (v) { v.play(); return true; }
                            return false;
                        }"""
                    )
                    if played:
                        clicked = True
                        break
                except Exception:
                    continue

        # Space 키 폴백: 포커스 된 플레이어에 Space 키로 재생
        if not clicked:
            try:
                await self.page.keyboard.press("Space")
                await self.page.wait_for_timeout(500)
                clicked = True
            except Exception:
                pass

        # 마우스 클릭 폴백: 뷰포트 중앙 클릭 (플레이어 썸네일 오버레이 영역)
        if not clicked:
            try:
                viewport = self.page.viewport_size or {"width": 1280, "height": 1024}
                await self.page.mouse.click(
                    viewport["width"] * 0.65,
                    viewport["height"] * 0.4,
                )
                clicked = True
            except Exception:
                pass

        if not clicked:
            return False

        await self.page.wait_for_timeout(3000)

        # 중단(일시정지) 버튼 클릭 (pauser-icon 클래스 최우선)
        pause_selectors = [
            # pause-icon 클래스 기반 (팝업토 플레이어)
            "[class*='pause-icon']",
            "button[class*='pause-icon']",
            # data-testid
            "[data-testid='player-pause']",
            "[data-testid='btn-pause']",
            "[data-testid='video-pause-button']",
            # aria-label
            "button[aria-label*='중단']",
            "button[aria-label*='일시정지']",
            "button[aria-label*='pause' i]",
            "button[title*='중단']",
            "button[title*='pause' i]",
            # class 기반 폴백
            "button[class*='pause']",
            "[class*='vjs-play-control']",
            "video",
        ]
        for _, ctx in contexts:
            for selector in pause_selectors:
                try:
                    loc = ctx.locator(selector).first
                    if await loc.count() > 0 and await loc.is_visible():
                        await loc.click()
                        break
                except Exception:
                    continue

        await self.page.wait_for_timeout(1000)
        return True

    async def _action_search(self) -> bool:
        """검색창에 '디지털' 입력 후 검색."""
        item = next(i for i in self.CHECKLIST if i.check_item == "검색 확인")
        contexts = await self._iter_contexts()
        for label, ctx in contexts:
            for selector in item.structural_selectors + [f"[data-testid='{t}']" for t in item.data_testids]:
                locator = ctx.locator(selector).first
                try:
                    if await locator.count() > 0 and await locator.is_visible():
                        await locator.click()
                        await self.page.wait_for_timeout(500)
                        await locator.fill("디지털")
                        await self.page.keyboard.press("Enter")
                        await self.mysuni_page.wait_for_page_loaded()
                        return True
                except Exception:
                    continue
        return False

    async def _action_badge_challenge(self) -> bool:
        """GNB Certification 메뉴 → Badge 탭 → 도전하기 클릭 → 도전중 배지 상세 진입 → 도전취소."""

        # Step 1: GNB Certification 메뉴 클릭
        cert_item = ChecklistItem(
            service="lms_pc",
            check_item="certification-nav",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["menu-certification", "nav-certification"],
            semantic_candidates=["Certification", "자격증", "배지"],
            structural_selectors=["a[href*='certification']", "a[href*='badge']"],
        )
        await self._click_with_priority(cert_item)
        await self.mysuni_page.wait_for_page_loaded()
        await self.page.wait_for_timeout(1000)

        # Step 2: Badge 탭 클릭
        badge_tab_item = ChecklistItem(
            service="lms_pc",
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
                "a[role='tab']:has-text('Badge')",
                "[class*='tab']:has-text('Badge')",
            ],
        )
        await self._click_with_priority(badge_tab_item)
        await self.page.wait_for_timeout(1000)

        # Step 3: 도전하기 — 전체 목록에서 "도전하기" 버튼 클릭
        challenge_ok = False
        contexts = await self._iter_contexts()
        for _, ctx in contexts:
            for selector in [
                "button:has-text('도전하기')",
                "button:has-text('도전 하기')",
                "[class*='badge'] button:has-text('도전')",
            ]:
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

        # Step 4: 도전 취소 — 전체 목록에서 "도전중" 버튼 클릭 → 상세 진입 → "도전취소" 클릭
        cancel_ok = False
        # 도전하기 후 팝업/모달이 열렸을 수 있으므로 닫기 처리
        for close_text in ["닫기", "확인", "취소"]:
            try:
                close_btn = self.page.locator(f"button:has-text('{close_text}')").last
                if await close_btn.count() > 0 and await close_btn.is_visible():
                    await close_btn.click()
                    await self.page.wait_for_timeout(500)
                    break
            except Exception:
                pass

        await self.page.wait_for_timeout(500)

        for _, ctx in contexts:
            for selector in [
                "button:has-text('도전중')",
                "[class*='badge'] button:has-text('도전중')",
            ]:
                try:
                    loc = ctx.locator(selector).first
                    if await loc.count() > 0 and await loc.is_visible():
                        await loc.click()
                        await self.mysuni_page.wait_for_page_loaded()
                        await self.page.wait_for_timeout(1000)
                        # 상세 화면에서 "도전취소" 버튼 클릭
                        cancel_btn = self.page.locator(
                            "button:has-text('도전취소'), button:has-text('도전 취소')"
                        ).first
                        if await cancel_btn.count() > 0 and await cancel_btn.is_visible():
                            await cancel_btn.click()
                            await self.page.wait_for_timeout(1000)
                            # 확인 다이얼로그 수락
                            confirm_btn = self.page.locator(
                                "button:has-text('확인'), button:has-text('예')"
                            ).first
                            if await confirm_btn.count() > 0 and await confirm_btn.is_visible():
                                await confirm_btn.click()
                                await self.page.wait_for_timeout(500)
                            cancel_ok = True
                        break
                except Exception:
                    continue
            if cancel_ok:
                break

        return challenge_ok or cancel_ok

    async def _action_community_post(self) -> bool:
        """게시글 작성 → 목록 확인 → 상세 이동 → 삭제 (상태 복원)."""
        # Community 메뉴로 이동
        comm_nav_item = ChecklistItem(
            service="lms_pc",
            check_item="community-nav",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["menu-community", "nav-community"],
            semantic_candidates=["Community", "커뮤니티"],
            structural_selectors=["a[href*='community']", "nav a:has-text('커뮤니티')"],
        )
        await self._click_with_priority(comm_nav_item)
        await self.mysuni_page.wait_for_page_loaded()
        await self.page.wait_for_timeout(1000)

        # 좌측 커뮤니티 목록에서 첫 번째 커뮤니티 게시판 진입
        board_item = ChecklistItem(
            service="lms_pc",
            check_item="community-board",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=[],
            semantic_candidates=[],
            structural_selectors=[
                "[class*='community'] li:first-child a",
                "[class*='board-list'] li:first-child a",
                "[class*='my-community'] li:first-child",
                "aside li:first-child a",
                "aside li:first-child",
            ],
        )
        await self._click_with_priority(board_item)
        await self.page.wait_for_timeout(1000)

        # 기존 테스트 게시글 정리 (stale post)
        await self._cleanup_stale_posts()

        # 페이지 상단으로 스크롤 후 글쓰기 클릭
        await self.page.evaluate("window.scrollTo(0, 0)")
        await self.page.wait_for_timeout(300)

        item = next(i for i in self.CHECKLIST if i.check_item == "커뮤니티 확인")
        # 추가 셀렉터 포함 임시 아이템으로 시도
        extended_item = ChecklistItem(
            service="lms_pc",
            check_item="community-write",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["btn-write-post", "community-write", "post-write"],
            semantic_candidates=["글쓰기", "작성", "새 글", "새글", "게시"],
            structural_selectors=[
                "button:has-text('글쓰기')",
                "button:has-text('작성')",
                "a:has-text('글쓰기')",
                "[class*='write'] button",
                "[class*='board-write']",
                "a[href*='/write']",
                "a[href*='/new']",
                "button[class*='create']",
            ],
        )
        if not await self._click_with_priority(extended_item):
            if not await self._click_with_priority(item):
                return False
        await self.page.wait_for_timeout(1500)

        # 제목/내용 입력
        title_input = self.page.locator("input[placeholder*='제목']").first
        content_input = self.page.locator("textarea, [contenteditable='true']").first
        try:
            if await title_input.count() > 0:
                await title_input.fill("[자동점검] LMS 커뮤니티 테스트 게시글")
            if await content_input.count() > 0:
                await content_input.fill("자동 점검 게시글입니다. 확인 후 삭제됩니다.")
        except Exception:
            pass

        # 등록 버튼 클릭
        submit_item = ChecklistItem(
            service="lms_pc",
            check_item="post-submit",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["btn-submit", "post-submit"],
            semantic_candidates=["등록", "게시", "저장"],
            structural_selectors=["button:has-text('등록')", "button:has-text('게시')", "button[type='submit']"],
        )
        if not await self._click_with_priority(submit_item):
            return False
        await self.mysuni_page.wait_for_page_loaded()
        await self.page.wait_for_timeout(1500)

        # 목록에서 방금 작성한 게시글 클릭
        post_link = self.page.get_by_text("[자동점검] LMS 커뮤니티 테스트 게시글").first
        try:
            if await post_link.count() > 0:
                await post_link.click()
                await self.mysuni_page.wait_for_page_loaded()
                await self.page.wait_for_timeout(1000)
        except Exception:
            pass

        # 삭제 처리
        delete_item = ChecklistItem(
            service="lms_pc",
            check_item="post-delete",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["btn-delete", "post-delete"],
            semantic_candidates=["삭제", "Delete"],
            structural_selectors=["button:has-text('삭제')", "a:has-text('삭제')"],
        )
        await self._click_with_priority(delete_item)
        await self.page.wait_for_timeout(500)

        # 삭제 확인 다이얼로그
        confirm_item = ChecklistItem(
            service="lms_pc",
            check_item="post-delete-confirm",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["btn-confirm", "confirm-ok"],
            semantic_candidates=["확인", "OK", "예"],
            structural_selectors=["button:has-text('확인')", "button:has-text('예')"],
        )
        await self._click_with_priority(confirm_item)
        await self.mysuni_page.wait_for_page_loaded()
        return True

    async def _cleanup_stale_posts(self) -> None:
        """이전 테스트 실행 중 삭제되지 않은 고아 게시글을 정리한다."""
        stale = self.page.get_by_text("[자동점검] LMS 커뮤니티 테스트 게시글").first
        try:
            if await stale.count() > 0:
                await stale.click()
                await self.mysuni_page.wait_for_page_loaded()
                delete_item = ChecklistItem(
                    service="lms_pc",
                    check_item="stale-delete",
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
                    service="lms_pc",
                    check_item="stale-delete-confirm",
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
                await self.page.wait_for_timeout(1000)
        except Exception:
            pass

    async def _action_logout(self) -> bool:
        """프로필 아이콘 클릭 → 로그아웃."""
        profile_item = ChecklistItem(
            service="lms_pc",
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
                "[class*='top'] [class*='user']",
            ],
        )
        profile_clicked = await self._click_with_priority(profile_item)
        if not profile_clicked:
            print("⚠️ 프로필 아이콘 클릭 실패 — 직접 로그아웃 버튼 탐색으로 전환")
        await self.page.wait_for_timeout(1000)

        # lg-out 클래스 우선 탐색 (드롭다운 내 로그아웃 요소)
        contexts = await self._iter_contexts()
        for _, ctx in contexts:
            for selector in [
                "[class*='lg-out']",
                "a[class*='lg-out']",
                "button[class*='lg-out']",
                "a[class*='logout']",
                "button[class*='logout']",
                "li:has-text('로그아웃') a",
                "li:has-text('로그아웃') button",
                "[class*='dropdown'] a:has-text('로그아웃')",
                "[class*='menu'] a:has-text('로그아웃')",
                "[class*='layer'] a:has-text('로그아웃')",
            ]:
                try:
                    loc = ctx.locator(selector).first
                    if await loc.count() > 0 and await loc.is_visible():
                        await loc.click()
                        await self.mysuni_page.wait_for_page_loaded()
                        if "login" in self.page.url:
                            return True
                except Exception:
                    continue

        # 폴백: 기존 4단계 클릭 전략 (URL 검증 포함)
        item = next(i for i in self.CHECKLIST if i.check_item == "로그아웃")
        if await self._click_with_priority(item):
            await self.mysuni_page.wait_for_page_loaded()
            if "login" in self.page.url:
                return True

        # JS 폴백: DOM 전체에서 로그아웃 텍스트 요소 직접 클릭 (URL 검증 포함)
        try:
            clicked = await self.page.evaluate("""
                () => {
                    const candidates = Array.from(document.querySelectorAll('a, button, li, span'));
                    for (const el of candidates) {
                        const text = (el.innerText || el.textContent || '').trim();
                        if (text === '로그아웃' || text === 'Logout' || text === 'Sign out') {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                el.click();
                                return true;
                            }
                        }
                    }
                    return false;
                }
            """)
            if clicked:
                await self.mysuni_page.wait_for_page_loaded()
                if "login" in self.page.url:
                    return True
        except Exception:
            pass

        return False
