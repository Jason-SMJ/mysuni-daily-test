"""
자동검증 7: Career Coach 1on1 페이지 테스트
"""

from pathlib import Path

from tests.base_test import BaseTest


class Career1on1TestScenario(BaseTest):
    SERVICE_KEY = "career_1on1"
    SCENARIO_NAME = "자동 검증 : Career Coach 1on1"
    SCREENSHOT_FILENAME = "screenshot_career_coach_1on1.png"
    PAGE_PATH = "/suni-main/career?page=/coach/one-on-one"

    def _resolve_reference_image(self) -> Path | None:
        path = Path("baselines") / self.SERVICE_KEY / self.SCREENSHOT_FILENAME
        return path if path.exists() else None
    
    async def run(self) -> bool:
        print(f"🚀 {self.SCENARIO_NAME} 시작")
        try:
            # 1. Career Coach 1on1 페이지로 이동
            if not await self.mysuni_page.goto_page(self.PAGE_PATH):
                return False
            
            # 2. 페이지 로딩 대기
            await self.mysuni_page.wait_for_page_loaded()
            
            # 3. 스크린샷 캡처
            screenshot_path = await self.take_screenshot(
                f"{self.SERVICE_KEY}/{self.SCREENSHOT_FILENAME}"
            )
            
            # 4. LLM으로 화면 검증
            result, llm_response = await self.validate_with_llm(
                screenshot_path,
                "strict",
                reference_image_path=self._resolve_reference_image(),
            )

            # 5. 비정상 감지 시 Slack 알림
            if result == "비정상":
                self.notify_failure(self.SCENARIO_NAME, llm_response, screenshot_path)
                return False
            
            print(f"✅ {self.SCENARIO_NAME} 완료 - {result}")
            return True
        
        except Exception as e:
            print(f"❌ {self.SCENARIO_NAME} 실패: {e}")
            return False
