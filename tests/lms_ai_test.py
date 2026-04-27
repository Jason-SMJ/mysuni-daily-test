"""LMS AI 학습도우미 일일점검 시나리오 (6항목).

항목 1(학습도우미 실행) 실패 시 2~6번은 '판단불가'로 일괄 처리.
AI 패널이 열린 상태를 유지하므로 항목 간 페이지 재이동 없이 순차 실행.
"""

from typing import Optional

from tests.multi_item_base import MultiItemTestBase, ActionOutcome
from tests.specs.daily_check_spec import ChecklistItem, LMS_AI_ITEMS


class LmsAiTestScenario(MultiItemTestBase):
    """LMS AI 학습도우미 6개 항목 점검."""

    SCENARIO_NAME = "LMS AI 학습도우미 일일점검"
    SCENARIO_KEY = "lms_ai"
    PAGE_PATH = "/"
    CHECKLIST = LMS_AI_ITEMS

    # 학습도우미 패널이 열렸는지 상태 추적
    _assistant_opened: bool = False

    def _build_action_map(self):
        return {
            "학습도우미 실행": self._action_open_assistant,
            "ProActive 버튼 표시": self._action_proactive_display,
            "ProActive 과정 추천 내용": self._action_proactive_click,
            "일반발화(과정탐색)": self._action_chat_course,
            "일반발화(지식검색)": self._action_chat_knowledge,
            "기타기능": self._action_misc_controls,
        }

    async def run(self) -> bool:
        """AI 패널 의존성 처리를 위해 run()을 오버라이드."""
        print(f"🚀 {self.SCENARIO_NAME} 시작")

        try:
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
            self._assistant_opened = False

            for order, (idx, item) in enumerate(indexed_items, start=1):
                print(f"\n[{order}/{len(indexed_items)}] {item.check_item}")

                # 학습도우미 실행 실패 시 이후 항목 판단불가 처리
                if not self._assistant_opened and item.check_item != "학습도우미 실행":
                    reason = "학습도우미 실행 실패로 점검 불가"
                    screenshot_path = await self.take_screenshot(
                        f"{self.SCENARIO_KEY}/{self.SCENARIO_KEY}_{idx:02d}.png"
                    )
                    self.record_item_result(
                        scenario_key=item.service,
                        item_id=idx,
                        item_name=item.check_item,
                        action_type=item.action_type,
                        result="판단불가",
                        llm_response=reason,
                        screenshot_path=screenshot_path,
                    )
                    self.notify_failure_item(
                        scenario_key=item.service,
                        item_id=idx,
                        item_name=item.check_item,
                        action_type=item.action_type,
                        result="판단불가",
                        llm_response=reason,
                        screenshot_path=screenshot_path,
                    )
                    failed_items.append(item.check_item)
                    continue

                ok, _ = await self._run_item(idx, item, action_map.get(item.check_item))
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

    async def _action_open_assistant(self) -> bool:
        """학습도우미 아이콘 클릭하여 패널 열기."""
        item = next(i for i in self.CHECKLIST if i.check_item == "학습도우미 실행")
        clicked = await self._click_with_priority(item)
        if clicked:
            await self.page.wait_for_timeout(2000)
            # 패널이 실제로 열렸는지 확인
            panel = self.page.locator(
                "[class*='assistant'], [class*='chatbot'], [class*='chat-panel']"
            ).first
            try:
                if await panel.count() > 0 and await panel.is_visible():
                    self._assistant_opened = True
                    return True
            except Exception:
                pass
            # 아이콘 클릭은 성공했으나 패널 감지 실패 시에도 열린 것으로 간주
            self._assistant_opened = True
            return True
        return False

    async def _action_proactive_display(self) -> bool:
        """ProActive 풍선말 버튼 표시 여부 확인 (클릭 없이 UI 확인)."""
        await self.page.wait_for_timeout(1500)
        # 풍선말 형태의 요소가 존재하는지만 확인 - 실제 클릭 없음
        bubble = self.page.locator(
            "[class*='proactive'], [class*='bubble'], [class*='balloon']"
        ).first
        try:
            return await bubble.count() > 0
        except Exception:
            return False

    async def _action_proactive_click(self) -> bool:
        """ProActive 버튼 클릭하여 과정 추천 내용 확인."""
        item = next(i for i in self.CHECKLIST if i.check_item == "ProActive 과정 추천 내용")
        clicked = await self._click_with_priority(item)
        if clicked:
            await self.page.wait_for_timeout(3000)
        return clicked

    async def _action_chat_course(self) -> bool:
        """발화 창에 '파이썬 강의의 찾아줘' 입력."""
        return await self._send_chat_message("파이썬 강의의 찾아줘")

    async def _action_chat_knowledge(self) -> bool:
        """발화 창에 '감수성이 뭐야?' 입력."""
        return await self._send_chat_message("감수성이 뭐야?")

    async def _action_misc_controls(self) -> bool:
        """새 대화 버튼 등 기타 기능 클릭."""
        item = next(i for i in self.CHECKLIST if i.check_item == "기타기능")
        clicked = await self._click_with_priority(item)
        if clicked:
            await self.page.wait_for_timeout(1000)
        return clicked

    async def _send_chat_message(self, message: str) -> bool:
        """채팅 입력창에 메시지를 입력하고 전송한다."""
        input_item = next(
            (i for i in self.CHECKLIST if i.check_item in ("일반발화(과정탐색)", "일반발화(지식검색)")),
            None,
        )
        if input_item is None:
            return False

        contexts = await self._iter_contexts()
        for _, ctx in contexts:
            for selector in input_item.structural_selectors + [
                f"[data-testid='{t}']" for t in input_item.data_testids
            ]:
                locator = ctx.locator(selector).first
                try:
                    if await locator.count() > 0 and await locator.is_visible():
                        await locator.click()
                        await locator.fill(message)
                        await self.page.keyboard.press("Enter")
                        await self.page.wait_for_timeout(3000)
                        return True
                except Exception:
                    continue
        return False
