"""LMS Mobile 일일점검 시나리오 (10항목).

iPhone 12 모바일 에뮬레이션 컨텍스트에서 실행.
main.py에서 browser_manager.new_mobile_page()로 생성한 페이지를 전달해야 한다.
"""

from tests.multi_item_base import MultiItemTestBase
from tests.specs.daily_check_spec import ChecklistItem, LMS_MOBILE_ITEMS


class LmsMobileTestScenario(MultiItemTestBase):
    """LMS Mobile 10개 항목 점검 (모바일 에뮬레이션)."""

    SCENARIO_NAME = "LMS Mobile 일일점검"
    SCENARIO_KEY = "lms_mobile"
    PAGE_PATH = "/mobile/app/install"
    CHECKLIST = LMS_MOBILE_ITEMS

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
        """모바일 컨텍스트는 별도 로그인이 필요하므로 run()을 오버라이드."""
        print(f"🚀 {self.SCENARIO_NAME} 시작")

        try:
            # 앱 설치 페이지 확인 (첫 이동)
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

    async def _action_login(self) -> bool:
        """LMS 로그인 페이지로 이동 후 로그인."""
        if not await self.mysuni_page.goto_page("/"):
            return False
        await self.mysuni_page.wait_for_page_loaded()
        item = next(i for i in self.CHECKLIST if i.check_item == "로그인")
        if await self._click_with_priority(item):
            await self.mysuni_page.wait_for_page_loaded()
            return True
        return False

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
        """배지 도전 팝업."""
        # 하단 전체 메뉴 → Certification
        cert_nav = ChecklistItem(
            service="lms_mobile",
            check_item="cert-nav",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["tab-certification", "menu-certification"],
            semantic_candidates=["Certification", "전체 메뉴"],
            structural_selectors=["a[href*='certification']", "[class*='tab']:has-text('Certification')"],
        )
        await self._click_with_priority(cert_nav)
        await self.mysuni_page.wait_for_page_loaded()
        await self.page.wait_for_timeout(1000)

        item = next(i for i in self.CHECKLIST if i.check_item == "배지 확인")
        return await self._action_popup(item, strict_testid_only=False)

    async def _action_community_post(self) -> bool:
        """커뮤니티 게시글 작성 후 삭제."""
        # 하단 커뮤니티 메뉴
        comm_nav = ChecklistItem(
            service="lms_mobile",
            check_item="community-nav",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["tab-community", "menu-community"],
            semantic_candidates=["커뮤니티", "Community"],
            structural_selectors=["a[href*='community']", "[class*='tab']:has-text('커뮤니티')"],
        )
        await self._click_with_priority(comm_nav)
        await self.mysuni_page.wait_for_page_loaded()
        await self.page.wait_for_timeout(1000)

        item = next(i for i in self.CHECKLIST if i.check_item == "커뮤니티 확인")
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
        """간편로그인 설정 (패턴 드로잉)."""
        # 하단 더보기 → 간편로그인 설정
        more_menu = ChecklistItem(
            service="lms_mobile",
            check_item="more-menu",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["tab-more", "menu-more"],
            semantic_candidates=["더보기", "More"],
            structural_selectors=["[class*='tab']:has-text('더보기')", "a:has-text('더보기')"],
        )
        await self._click_with_priority(more_menu)
        await self.page.wait_for_timeout(500)

        item = next(i for i in self.CHECKLIST if i.check_item == "간편로그인 설정")
        if not await self._click_with_priority(item):
            return False
        await self.page.wait_for_timeout(1000)

        # 패턴 선택 (3x3 그리드 패턴: L 자 패턴 1→2→3→6→9)
        pattern_canvas = self.page.locator("[class*='pattern'], canvas").first
        try:
            if await pattern_canvas.count() > 0:
                box = await pattern_canvas.bounding_box()
                if box:
                    cell_w = box["width"] / 3
                    cell_h = box["height"] / 3
                    points = [
                        (box["x"] + cell_w * 0.5, box["y"] + cell_h * 0.5),   # 1
                        (box["x"] + cell_w * 1.5, box["y"] + cell_h * 0.5),   # 2
                        (box["x"] + cell_w * 2.5, box["y"] + cell_h * 0.5),   # 3
                        (box["x"] + cell_w * 2.5, box["y"] + cell_h * 1.5),   # 6
                        (box["x"] + cell_w * 2.5, box["y"] + cell_h * 2.5),   # 9
                    ]
                    await self.page.mouse.move(points[0][0], points[0][1])
                    await self.page.mouse.down()
                    for px, py in points[1:]:
                        await self.page.mouse.move(px, py)
                        await self.page.wait_for_timeout(100)
                    await self.page.mouse.up()
                    await self.page.wait_for_timeout(1000)

                    # 동일 패턴 재입력
                    await self.page.mouse.move(points[0][0], points[0][1])
                    await self.page.mouse.down()
                    for px, py in points[1:]:
                        await self.page.mouse.move(px, py)
                        await self.page.wait_for_timeout(100)
                    await self.page.mouse.up()
                    await self.page.wait_for_timeout(1500)
                    return True
        except Exception as e:
            print(f"⚠️ 패턴 드로잉 실패: {e}")
        return False

    async def _action_logout(self) -> bool:
        """하단 더보기 → 로그아웃."""
        more_menu = ChecklistItem(
            service="lms_mobile",
            check_item="more-menu",
            check_detail="",
            expected_result="",
            mode="playwright",
            action_type="click",
            data_testids=["tab-more", "menu-more"],
            semantic_candidates=["더보기", "More"],
            structural_selectors=["[class*='tab']:has-text('더보기')", "a:has-text('더보기')"],
        )
        await self._click_with_priority(more_menu)
        await self.page.wait_for_timeout(500)

        item = next(i for i in self.CHECKLIST if i.check_item == "로그아웃")
        if await self._click_with_priority(item):
            await self.mysuni_page.wait_for_page_loaded()
            return True
        return False

    async def _action_easy_login(self) -> bool:
        """간편 로그인 버튼 클릭 후 패턴 입력."""
        item = next(i for i in self.CHECKLIST if i.check_item == "간편로그인")
        if not await self._click_with_priority(item):
            return False
        await self.page.wait_for_timeout(1000)

        # 이전 설정과 동일한 패턴(1→2→3→6→9) 입력
        pattern_canvas = self.page.locator("[class*='pattern'], canvas").first
        try:
            if await pattern_canvas.count() > 0:
                box = await pattern_canvas.bounding_box()
                if box:
                    cell_w = box["width"] / 3
                    cell_h = box["height"] / 3
                    points = [
                        (box["x"] + cell_w * 0.5, box["y"] + cell_h * 0.5),
                        (box["x"] + cell_w * 1.5, box["y"] + cell_h * 0.5),
                        (box["x"] + cell_w * 2.5, box["y"] + cell_h * 0.5),
                        (box["x"] + cell_w * 2.5, box["y"] + cell_h * 1.5),
                        (box["x"] + cell_w * 2.5, box["y"] + cell_h * 2.5),
                    ]
                    await self.page.mouse.move(points[0][0], points[0][1])
                    await self.page.mouse.down()
                    for px, py in points[1:]:
                        await self.page.mouse.move(px, py)
                        await self.page.wait_for_timeout(100)
                    await self.page.mouse.up()
                    await self.page.wait_for_timeout(2000)
                    return True
        except Exception as e:
            print(f"⚠️ 간편로그인 패턴 입력 실패: {e}")
        return False
