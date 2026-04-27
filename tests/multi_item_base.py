"""다중 항목 체크리스트 시나리오 공통 베이스 클래스.

career_profile_test.py의 클릭 전략·모달 감지·반복 루프 엔진을 추출하여
LMS_PC, LMS_AI, LMS_Mobile, Career확장, One_ID 등 모든 체크리스트 시나리오가
공유하는 기반을 제공한다.
"""

import asyncio
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Callable, Optional, Awaitable, Any

from tests.base_test import BaseTest
from tests.specs.daily_check_spec import ChecklistItem


@dataclass
class ActionOutcome:
    ok: bool
    transition_type: str = "none"
    context: str = ""
    selector: str = ""
    reason: str = ""
    capture_locator: Any | None = None
    capture_context: Any | None = None


class MultiItemTestBase(BaseTest):
    """다중 체크리스트 항목을 순회하는 시나리오의 공통 엔진.

    서브클래스는 반드시 SCENARIO_NAME, SCENARIO_KEY, PAGE_PATH, CHECKLIST를 정의하고
    _build_action_map()을 오버라이드한다.
    """

    SCENARIO_NAME: str = ""
    SCENARIO_KEY: str = ""
    PAGE_PATH: str = "/"
    CHECKLIST: list[ChecklistItem] = []

    MODAL_CLASS_SELECTOR = "[class*='BaseModal_main__']"
    POPUP_SELECTORS = [MODAL_CLASS_SELECTOR]

    def __init__(self, *args, target_item_index: int | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_item_index = target_item_index
        self._last_click_trace = "no-click"
        self._last_popup_context = ""
        self._last_action_outcome = ActionOutcome(ok=False)
        self._last_capture_error = ""

    # ──────────────────────────────────────────────
    # 서브클래스 오버라이드 포인트
    # ──────────────────────────────────────────────

    def _build_action_map(self) -> dict[str, Callable[[], Awaitable[bool]]]:
        """항목명 → 사전 동작 함수 매핑. 서브클래스에서 오버라이드."""
        return {}

    def _item_slug(self, item: ChecklistItem) -> str:
        """디버그 파일명에 쓸 슬러그. 서브클래스에서 오버라이드 가능."""
        return item.check_item.replace(" ", "_").replace("/", "-")[:30]

    def _popup_title_candidates(self, item: ChecklistItem) -> list[str]:
        """팝업 제목 후보 문자열 목록. 서브클래스에서 항목별로 오버라이드 가능."""
        return []

    def _build_prompt(self, item: ChecklistItem, action_ok: Optional[bool]) -> str:
        """LLM 검증용 프롬프트 생성. 서브클래스에서 오버라이드 가능."""
        action_note = "실행 없음"
        if action_ok is True:
            action_note = "클릭/진입 시도 성공"
        elif action_ok is False:
            action_note = "클릭/진입 시도 실패"

        return (
            "아래 체크 항목 기준으로 스크린샷이 정상인지 판별해줘.\n"
            f"- 점검 항목: {item.check_item}\n"
            f"- 점검 상세: {item.check_detail}\n"
            f"- 기대 결과: {item.expected_result}\n"
            f"- 사전 동작 결과: {action_note}\n"
            f"- 전환 타입: {self._last_action_outcome.transition_type}\n"
            "- 비교 방식: 기준 이미지와 실행 결과 이미지를 비교해 판정한다(기준 이미지가 없으면 실행 결과만 판정).\n"
            "- 추가 정상 기준: 데이터가 없어도 정책/안내 문구가 보이면 정상으로 본다.\n"
            "- 추가 비정상 기준: 깨짐/로딩만/오류 화면이면 비정상이다.\n"
            "판정 기준: 기대 결과가 명확히 보이면 '정상', 아니면 '비정상'이라고 답해."
        )

    async def _post_item_hook(self, item: ChecklistItem) -> None:
        """각 항목 실행 후 호출되는 훅. 서브클래스에서 오버라이드 가능."""

    # ──────────────────────────────────────────────
    # 컨텍스트·스냅샷
    # ──────────────────────────────────────────────

    async def _iter_contexts(self) -> list[tuple[str, Any]]:
        contexts: list[tuple[str, Any]] = [("main", self.page)]
        for idx, frame in enumerate(self.page.frames):
            if frame == self.page.main_frame:
                continue
            label = frame.name or f"frame-{idx}"
            contexts.append((f"frame:{label}", frame))
        return contexts

    async def _snapshot_context(self, ctx: Any) -> dict[str, Any]:
        js = """
        () => {
          const isVisible = (el) => {
            if (!el) return false;
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
          };

          const pickText = (el) => (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 120);

          const headings = Array.from(document.querySelectorAll('h1,h2,h3,h4,[role="heading"]'))
            .filter(isVisible)
            .map(pickText)
            .filter(Boolean)
            .slice(0, 30);

          const buttons = Array.from(document.querySelectorAll('button,[role="button"],a'))
            .filter(isVisible)
            .map((el) => ({
              text: pickText(el),
              testid: el.getAttribute('data-testid') || '',
              aria: el.getAttribute('aria-label') || ''
            }))
            .filter((v) => v.text || v.testid || v.aria)
            .slice(0, 60);

          const popupCandidates = Array.from(
            document.querySelectorAll("[class*='BaseModal_main__'], [role='dialog'], .modal, .drawer, .popup, .dialog, .layer-popup")
          )
            .filter(isVisible)
            .map((el) => ({
              tag: el.tagName,
              className: (el.className || '').toString().slice(0, 120),
              text: pickText(el),
            }))
            .slice(0, 20);

          const formFieldsVisible = Array.from(document.querySelectorAll('input,textarea,select,[contenteditable="true"]'))
            .filter(isVisible)
            .length;

          return {
            title: document.title,
            url: location.href,
            headings,
            buttons,
            popupCandidates,
            formFieldsVisible,
          };
        }
        """
        try:
            return await ctx.evaluate(js)
        except Exception as e:
            return {"error": str(e)}

    async def _dump_popup_debug(self, item: ChecklistItem, phase: str) -> None:
        if item.action_type != "popup":
            return

        debug_dir = Path("screenshots") / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)

        contexts = await self._iter_contexts()
        snapshots: list[dict[str, Any]] = []
        for label, ctx in contexts:
            snapshots.append(
                {
                    "context": label,
                    "snapshot": await self._snapshot_context(ctx),
                }
            )

        payload = {
            "item": item.check_item,
            "phase": phase,
            "click_trace": self._last_click_trace,
            "popup_trace": self._last_popup_context,
            "action_outcome": {
                "ok": self._last_action_outcome.ok,
                "transition_type": self._last_action_outcome.transition_type,
                "context": self._last_action_outcome.context,
                "selector": self._last_action_outcome.selector,
                "reason": self._last_action_outcome.reason,
            },
            "contexts": snapshots,
        }

        out = debug_dir / f"{self._item_slug(item)}_{phase}.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"🧭 팝업 디버그 덤프 저장: {out}")

    # ──────────────────────────────────────────────
    # 4단계 클릭 전략
    # ──────────────────────────────────────────────

    async def _click_by_testid(self, ctx: Any, testids: list[str]) -> bool:
        for testid in testids:
            selector = f"[data-testid='{testid}']"
            locator = ctx.locator(selector).first
            try:
                if await locator.count() > 0 and await locator.is_visible():
                    await locator.scroll_into_view_if_needed()
                    await locator.click(timeout=3000)
                    self._last_click_trace = f"source=data-testid selector={selector}"
                    return True
            except Exception:
                continue
        return False

    async def _click_by_semantic(self, ctx: Any, candidates: list[str]) -> bool:
        for text in candidates:
            locator = ctx.get_by_text(text, exact=False).first
            try:
                if await locator.count() > 0 and await locator.is_visible():
                    await locator.scroll_into_view_if_needed()
                    await locator.click(timeout=3000)
                    self._last_click_trace = f"source=semantic text={text}"
                    return True
            except Exception:
                continue
        return False

    async def _click_by_structural(self, ctx: Any, selectors: list[str]) -> bool:
        for selector in selectors:
            locator = ctx.locator(selector).first
            try:
                if await locator.count() > 0 and await locator.is_visible():
                    await locator.scroll_into_view_if_needed()
                    await locator.click(timeout=3000)
                    self._last_click_trace = f"source=structural selector={selector}"
                    return True
            except Exception:
                continue
        return False

    async def _js_fallback_click(self, ctx: Any, selectors: list[str]) -> bool:
        js = """
        (selectors) => {
          for (const selector of selectors) {
            const nodes = Array.from(document.querySelectorAll(selector));
            for (const node of nodes) {
              const rect = node.getBoundingClientRect();
              const visible = rect.width > 0 && rect.height > 0;
              if (visible) {
                node.click();
                return true;
              }
            }
          }
          return false;
        }
        """
        try:
            clicked = bool(await ctx.evaluate(js, selectors))
            if clicked:
                self._last_click_trace = f"source=js-fallback selectors={selectors}"
            return clicked
        except Exception:
            return False

    async def _click_with_priority(self, item: ChecklistItem, strict_testid_only: bool = False) -> bool:
        self._last_click_trace = "no-click"
        contexts = await self._iter_contexts()

        for label, ctx in contexts:
            if item.data_testids and await self._click_by_testid(ctx, item.data_testids):
                self._last_click_trace += f" context={label}"
                await self.page.wait_for_timeout(1000)
                return True

        if strict_testid_only:
            return False

        for label, ctx in contexts:
            if item.semantic_candidates and await self._click_by_semantic(ctx, item.semantic_candidates):
                self._last_click_trace += f" context={label}"
                await self.page.wait_for_timeout(1000)
                return True

        for label, ctx in contexts:
            if item.structural_selectors and await self._click_by_structural(ctx, item.structural_selectors):
                self._last_click_trace += f" context={label}"
                await self.page.wait_for_timeout(1000)
                return True

        js_selectors = [
            *[f"[data-testid='{v}']" for v in item.data_testids],
            *item.structural_selectors,
        ]
        for label, ctx in contexts:
            if js_selectors and await self._js_fallback_click(ctx, js_selectors):
                self._last_click_trace += f" context={label}"
                await self.page.wait_for_timeout(1000)
                return True

        return False

    # ──────────────────────────────────────────────
    # 팝업·모달 감지 및 닫기
    # ──────────────────────────────────────────────

    async def _ensure_item_section_visible(self, item: ChecklistItem) -> None:
        titles = self._popup_title_candidates(item)
        if not titles:
            return

        contexts = await self._iter_contexts()
        for _, ctx in contexts:
            for title in titles:
                heading = ctx.locator(
                    ", ".join(
                        [
                            f"h1:has-text('{title}')",
                            f"h2:has-text('{title}')",
                            f"h3:has-text('{title}')",
                            f"[role='heading']:has-text('{title}')",
                        ]
                    )
                ).first
                try:
                    if await heading.count() > 0:
                        await heading.scroll_into_view_if_needed()
                        await self.page.wait_for_timeout(500)
                        return
                except Exception:
                    continue

    async def _find_item_popup_locator(self, item: ChecklistItem) -> "ActionOutcome | None":
        contexts = await self._iter_contexts()
        title_candidates = self._popup_title_candidates(item)
        for label, ctx in contexts:
            modals = ctx.locator(self.MODAL_CLASS_SELECTOR)
            try:
                count = await modals.count()
            except Exception:
                continue

            best_idx = -1
            best_score = -1
            best_title_hit = False

            for idx in range(count):
                modal = modals.nth(idx)
                try:
                    if not await modal.is_visible():
                        continue

                    info = await modal.evaluate(
                        """
                        (el, titleCandidates) => {
                          const text = (el.innerText || el.textContent || '').trim();
                          const fields = el.querySelectorAll('input, textarea, select, button').length;
                          const rect = el.getBoundingClientRect();
                          const enoughSize = rect.width >= 320 && rect.height >= 200;
                          const hasMeaningfulText = text.replace(/\\s+/g, ' ').length >= 8;
                          const textLen = text.replace(/\\s+/g, ' ').length;
                          const normalized = text.replace(/\\s+/g, ' ').toLowerCase();
                          const titleHit = (titleCandidates || []).some((title) => {
                            const key = String(title || '').replace(/\\s+/g, ' ').toLowerCase();
                            return key && normalized.includes(key);
                          });
                          const score = (fields * 10) + textLen;
                          return { enoughSize, hasMeaningfulText, fields, textLen, score, titleHit };
                        }
                        """,
                        title_candidates,
                    )
                    content_ready = bool(
                        info
                        and info.get("enoughSize")
                        and (info.get("hasMeaningfulText") or int(info.get("fields", 0)) > 0)
                    )
                    if not content_ready:
                        continue

                    score = int(info.get("score", 0))
                    title_hit = bool(info.get("titleHit"))
                    should_update = False
                    if title_hit and not best_title_hit:
                        should_update = True
                    elif title_hit == best_title_hit and score > best_score:
                        should_update = True

                    if should_update:
                        best_title_hit = title_hit
                        best_score = score
                        best_idx = idx
                except Exception:
                    continue

            if best_idx >= 0:
                modal = modals.nth(best_idx)
                try:
                    return ActionOutcome(
                        ok=True,
                        transition_type="popup",
                        context=label,
                        selector=f"{self.MODAL_CLASS_SELECTOR}:nth({best_idx})",
                        capture_locator=modal,
                        capture_context=ctx,
                    )
                except Exception:
                    continue

        return None

    async def _detect_transition(
        self,
        item: ChecklistItem,
        before_url: str,
        before_page_count: int,
        timeout_ms: int = 5000,
    ) -> ActionOutcome:
        popup_candidates = self.POPUP_SELECTORS
        elapsed = 0
        interval = 300
        while elapsed <= timeout_ms:
            targeted_popup = await self._find_item_popup_locator(item)
            if targeted_popup is not None:
                return targeted_popup

            contexts = await self._iter_contexts()
            for label, ctx in contexts:
                for selector in popup_candidates:
                    locator = ctx.locator(selector).first
                    try:
                        if await locator.count() > 0 and await locator.is_visible():
                            return ActionOutcome(
                                ok=True,
                                transition_type="popup",
                                context=label,
                                selector=selector,
                                capture_locator=locator,
                                capture_context=ctx,
                            )
                    except Exception:
                        continue

            if self.page.url != before_url:
                return ActionOutcome(
                    ok=False,
                    transition_type="navigation",
                    context="main",
                    selector="url-changed",
                    reason=f"팝업 대신 URL 변경 발생: before={before_url} after={self.page.url}",
                )

            if len(self.page.context.pages) > before_page_count:
                return ActionOutcome(
                    ok=False,
                    transition_type="new-page",
                    context="browser",
                    selector="context.pages increased",
                    reason="팝업 대신 새 페이지 열림",
                )

            await self.page.wait_for_timeout(interval)
            elapsed += interval

        return ActionOutcome(
            ok=False,
            transition_type="none",
            reason="click 이후 BaseModal 모달 전환이 감지되지 않음",
        )

    async def _action_popup(self, item: ChecklistItem, strict_testid_only: bool = True) -> bool:
        dialog_seen = {"opened": False}
        before_url = self.page.url
        before_page_count = len(self.page.context.pages)

        await self._close_all_popups(item)
        await self._ensure_item_section_visible(item)
        await self._dump_popup_debug(item, "before_click")

        def _on_dialog(dialog):
            dialog_seen["opened"] = True
            asyncio.create_task(dialog.accept())

        self.page.once("dialog", _on_dialog)

        opened = await self._click_with_priority(item, strict_testid_only=strict_testid_only)
        await self._dump_popup_debug(item, "after_click")
        if not opened and not dialog_seen["opened"]:
            self._last_action_outcome = ActionOutcome(
                ok=False,
                transition_type="none",
                reason="클릭 실패",
            )
            print(f"❌ 팝업 열기 실패: {item.check_item} ({self._last_click_trace})")
            await self._dump_popup_debug(item, "click_failed")
            return False

        outcome = await self._detect_transition(item, before_url, before_page_count, timeout_ms=6000)

        if dialog_seen["opened"] and not outcome.ok:
            outcome = ActionOutcome(
                ok=False,
                transition_type="browser-dialog",
                context="main",
                selector="dialog.accept()",
                reason="브라우저 dialog는 모달 캡처 대상이 아님",
            )

        self._last_action_outcome = outcome
        self._last_popup_context = (
            f"context={outcome.context} selector={outcome.selector}"
            if outcome.ok
            else ""
        )

        if not outcome.ok:
            print(
                f"❌ 팝업 가시성/전환 확인 실패: {item.check_item} "
                f"(click={self._last_click_trace}, reason={outcome.reason}, browser_dialog={dialog_seen['opened']})"
            )
            await self._dump_popup_debug(item, "transition_failed")
            return False

        print(
            f"✅ 전환 감지: {item.check_item} "
            f"(type={outcome.transition_type}, context={outcome.context}, selector={outcome.selector})"
        )
        await self._dump_popup_debug(item, "transition_success")
        return True

    async def _wait_for_popup_visible(self, timeout_ms: int = 5000) -> bool:
        contexts = await self._iter_contexts()
        for label, ctx in contexts:
            for selector in self.POPUP_SELECTORS:
                locator = ctx.locator(selector).first
                try:
                    await locator.wait_for(state="visible", timeout=timeout_ms)
                    self._last_popup_context = f"context={label} selector={selector}"
                    return True
                except Exception:
                    continue
        self._last_popup_context = ""
        return False

    async def _close_popup(self, item: ChecklistItem) -> None:
        close_item = ChecklistItem(
            service=item.service,
            check_item=f"{item.check_item}-close",
            check_detail="",
            expected_result="",
            mode=item.mode,
            action_type="click",
            data_testids=["modal-close", "dialog-close", "btn-close"],
            semantic_candidates=item.popup_close_candidates or ["닫기", "취소", "Close", "X"],
            structural_selectors=[
                "[role='dialog'] button[aria-label='Close']",
                "[role='dialog'] .close",
                ".modal .btn-close",
                ".popup .btn-close",
            ],
        )
        _ = await self._click_with_priority(close_item)
        try:
            await self.page.keyboard.press("Escape")
        except Exception:
            pass

    async def _visible_modal_count(self) -> int:
        contexts = await self._iter_contexts()
        total = 0
        for _, ctx in contexts:
            modals = ctx.locator(self.MODAL_CLASS_SELECTOR)
            try:
                count = await modals.count()
            except Exception:
                continue

            for idx in range(count):
                try:
                    if await modals.nth(idx).is_visible():
                        total += 1
                except Exception:
                    continue
        return total

    async def _close_all_popups(self, item: ChecklistItem, max_rounds: int = 4) -> None:
        for _ in range(max_rounds):
            visible_before = await self._visible_modal_count()
            if visible_before == 0:
                return

            await self._close_popup(item)
            await self.page.wait_for_timeout(350)

            visible_after = await self._visible_modal_count()
            if visible_after == 0:
                return
            if visible_after >= visible_before:
                try:
                    await self.page.keyboard.press("Escape")
                except Exception:
                    pass
                await self.page.wait_for_timeout(250)

    # ──────────────────────────────────────────────
    # 스크린샷 캡처
    # ──────────────────────────────────────────────

    async def _capture_popup_screenshot(self, item: ChecklistItem, filename: str) -> Path | None:
        outcome = self._last_action_outcome
        if outcome.ok and outcome.transition_type == "popup" and outcome.capture_locator is not None:
            try:
                title_candidates = [
                    v.lower().replace(" ", "")
                    for v in self._popup_title_candidates(item)
                ]

                ready = False
                for _ in range(32):
                    try:
                        visible = await outcome.capture_locator.is_visible()
                    except Exception:
                        visible = False

                    if not visible:
                        await self.page.wait_for_timeout(250)
                        continue

                    try:
                        info = await outcome.capture_locator.evaluate(
                            """
                            (el) => {
                              const text = (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' ');
                              const normalized = text.toLowerCase().replace(/\\s+/g, '');
                              const fields = el.querySelectorAll('input, textarea, select, button').length;
                              const rect = el.getBoundingClientRect();
                              return {
                                textLen: text.length,
                                normalized,
                                fields,
                                width: rect.width,
                                height: rect.height
                              };
                            }
                            """
                        )
                    except Exception:
                        info = None

                    if info:
                        text_len = int(info.get("textLen", 0))
                        fields = int(info.get("fields", 0))
                        width = float(info.get("width", 0))
                        height = float(info.get("height", 0))
                        normalized = str(info.get("normalized", ""))
                        title_hit = (
                            any(t and t in normalized for t in title_candidates)
                            if title_candidates
                            else True
                        )
                        if width >= 320 and height >= 180 and (fields > 0 or text_len >= 20) and title_hit:
                            ready = True
                            break

                    await self.page.wait_for_timeout(250)

                if not ready:
                    raise RuntimeError("모달 콘텐츠 렌더 대기 타임아웃")

                await self.page.wait_for_timeout(300)

                min_reasonable_size = 20_000
                try:
                    for attempt in range(1, 4):
                        path = self.screenshot_manager.output_dir / filename
                        await outcome.capture_locator.screenshot(path=str(path), animations="disabled")
                        size = path.stat().st_size if path.exists() else 0
                        if size >= min_reasonable_size:
                            print(f"📸 타깃 모달 요소 캡처 저장 완료: {path}")
                            return path
                        print(f"⚠️ 모달 요소 캡처 재시도: 파일 크기 과소({size} bytes), attempt={attempt}/3")
                        await self.page.wait_for_timeout(250)
                except Exception as modal_capture_error:
                    print(f"⚠️ 모달 요소 캡처 실패, iframe/page 폴백 진행: {modal_capture_error}")

                frame_ctx = outcome.capture_context
                if frame_ctx is not None and hasattr(frame_ctx, "frame_element"):
                    try:
                        frame_el = await frame_ctx.frame_element()
                        for attempt in range(1, 4):
                            await frame_el.scroll_into_view_if_needed()
                            path = self.screenshot_manager.output_dir / filename
                            await frame_el.screenshot(path=str(path), animations="disabled")
                            size = path.stat().st_size if path.exists() else 0
                            if size >= min_reasonable_size:
                                print(f"📸 iframe 전체영역 캡처 저장 완료: {path}")
                                return path
                            print(f"⚠️ iframe 캡처 재시도: 파일 크기 과소({size} bytes), attempt={attempt}/3")
                            await self.page.wait_for_timeout(300)
                    except Exception as iframe_error:
                        print(f"⚠️ iframe 전체영역 캡처 실패: {iframe_error}")

                for attempt in range(1, 4):
                    captured = await self.screenshot_manager.capture_full_page(self.page, filename)
                    size = captured.stat().st_size if captured.exists() else 0
                    if size >= min_reasonable_size:
                        return captured
                    print(f"⚠️ page full_page 캡처 재시도: 파일 크기 과소({size} bytes), attempt={attempt}/3")
                    await self.page.wait_for_timeout(300)

                raise RuntimeError("full_page 캡처 결과가 비정상적으로 작음")
            except Exception as e:
                self._last_capture_error = str(e)
                print(f"❌ 팝업 캡처 예외: {e}")

        return None

    def _resolve_reference_image(self, item: ChecklistItem) -> Path | None:
        if not item.reference_image:
            return None
        path = Path("baselines") / item.reference_image
        return path if path.exists() else None

    # ──────────────────────────────────────────────
    # 항목 실행 루프
    # ──────────────────────────────────────────────

    async def _run_item(
        self,
        idx: int,
        item: ChecklistItem,
        action: Optional[Callable[[], Awaitable[bool]]] = None,
    ) -> tuple[bool, str]:
        self._last_popup_context = ""
        self._last_action_outcome = ActionOutcome(ok=False)
        self._last_capture_error = ""
        action_ok: Optional[bool] = None
        if action is not None:
            action_ok = await action()

        await self.mysuni_page.wait_for_page_loaded()
        await self.page.wait_for_timeout(1000)

        filename = (
            item.reference_image
            if item.reference_image
            else f"{self.SCENARIO_KEY}/{self.SCENARIO_KEY}_{idx:02d}.png"
        )
        screenshot_path: Path
        if item.action_type == "popup":
            popup_capture = await self._capture_popup_screenshot(item, filename)
            if not popup_capture:
                screenshot_path = await self.take_screenshot(filename)
                detail = (
                    f"체크항목: {item.check_item}\n"
                    f"사전동작: {'성공' if action_ok is True else '실패' if action_ok is False else '없음'}\n"
                    f"클릭추적: {self._last_click_trace}\n"
                    f"전환타입: {self._last_action_outcome.transition_type}\n"
                    f"팝업추적: {self._last_popup_context or 'N/A'}\n"
                    f"캡처오류: {self._last_capture_error or 'N/A'}"
                )
                self.record_item_result(
                    scenario_key=item.service,
                    item_id=idx,
                    item_name=item.check_item,
                    action_type=item.action_type,
                    result="판단불가",
                    llm_response=detail,
                    screenshot_path=screenshot_path,
                )
                self.notify_failure_item(
                    scenario_key=item.service,
                    item_id=idx,
                    item_name=item.check_item,
                    action_type=item.action_type,
                    result="판단불가",
                    llm_response=detail,
                    screenshot_path=screenshot_path,
                )
                print(
                    f"❌ 팝업 캡처 실패: {item.check_item} "
                    f"(click={self._last_click_trace}, transition={self._last_action_outcome.transition_type}, "
                    f"popup={self._last_popup_context or 'not-found'})"
                )
                return False, "팝업 요소 캡처 실패"
            screenshot_path = popup_capture
        else:
            screenshot_path = await self.take_screenshot(filename)

        result, llm_response = await self.validate_with_llm(
            screenshot_path,
            validation_mode="strict",
            custom_prompt=self._build_prompt(item, action_ok),
            reference_image_path=self._resolve_reference_image(item),
        )

        self.record_item_result(
            scenario_key=item.service,
            item_id=idx,
            item_name=item.check_item,
            action_type=item.action_type,
            result=result,
            llm_response=llm_response,
            screenshot_path=screenshot_path,
        )

        if result != "정상":
            detail = (
                f"체크항목: {item.check_item}\n"
                f"사전동작: {'성공' if action_ok is True else '실패' if action_ok is False else '없음'}\n"
                f"클릭추적: {self._last_click_trace}\n"
                f"전환타입: {self._last_action_outcome.transition_type}\n"
                f"팝업추적: {self._last_popup_context or 'N/A'}\n"
                f"LLM: {llm_response}"
            )
            self.notify_failure_item(
                scenario_key=item.service,
                item_id=idx,
                item_name=item.check_item,
                action_type=item.action_type,
                result=result,
                llm_response=detail,
                screenshot_path=screenshot_path,
            )
            return False, llm_response

        return True, llm_response

    async def run(self) -> bool:
        print(f"🚀 {self.SCENARIO_NAME} 시작")

        try:
            if not await self.mysuni_page.goto_page(self.PAGE_PATH):
                return False
            await self.mysuni_page.wait_for_page_loaded()

            action_map = self._build_action_map()

            indexed_items = list(enumerate(self.CHECKLIST, start=1))
            if self.target_item_index is not None:
                indexed_items = [
                    (idx, checklist_item)
                    for idx, checklist_item in indexed_items
                    if idx == self.target_item_index
                ]
                if not indexed_items:
                    print(
                        f"❌ 잘못된 item 인덱스: {self.target_item_index} "
                        f"(유효 범위: 1~{len(self.CHECKLIST)})"
                    )
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

            print(f"✅ {self.SCENARIO_NAME} 완료 - {len(indexed_items)}개 항목 통과")
            return True

        except Exception as e:
            print(f"❌ {self.SCENARIO_NAME} 실패: {e}")
            return False
