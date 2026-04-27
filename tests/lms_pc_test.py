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
        """카드 상세 LNB에서 Video 큐브 클릭."""
        item = next(i for i in self.CHECKLIST if i.check_item == "큐브 확인")
        if await self._click_with_priority(item):
            await self.mysuni_page.wait_for_page_loaded()
            return True
        return False

    async def _action_play_video(self) -> bool:
        """재생 버튼 클릭 후 중단 버튼 클릭."""
        item = next(i for i in self.CHECKLIST if i.check_item == "영상 확인")
        if not await self._click_with_priority(item):
            return False
        await self.page.wait_for_timeout(3000)

        pause_item = ChecklistItem(
            service="lms_pc",
            check_item="영상 중단",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["player-pause", "btn-pause", "video-pause-button"],
            semantic_candidates=["중단", "일시정지", "Pause"],
            structural_selectors=[
                "button[aria-label*='중단']",
                "button[aria-label*='pause' i]",
                "button[aria-label*='일시정지']",
            ],
        )
        await self._click_with_priority(pause_item)
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
        """배지 도전 → 스크린샷 → 도전 취소 (상태 복원)."""
        item = next(i for i in self.CHECKLIST if i.check_item == "배지 확인")

        # Certification 메뉴로 먼저 이동
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

        # 배지 도전 팝업
        return await self._action_popup(item, strict_testid_only=False)

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

        # 기존 테스트 게시글 정리 (stale post)
        await self._cleanup_stale_posts()

        # 글쓰기 클릭
        item = next(i for i in self.CHECKLIST if i.check_item == "커뮤니티 확인")
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
            ],
        )
        await self._click_with_priority(profile_item)
        await self.page.wait_for_timeout(500)

        item = next(i for i in self.CHECKLIST if i.check_item == "로그아웃")
        if await self._click_with_priority(item):
            await self.mysuni_page.wait_for_page_loaded()
            return True
        return False
