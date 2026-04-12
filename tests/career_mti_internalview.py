"""
자동검증 5: Career Recommend 페이지 테스트
커리어 추천 페이지의 AI 기능이 정상 작동하는지 검증합니다.
"""

from tests.base_test import BaseTest


class CareerMTIInternalViewTestScenario(BaseTest):
    """Career MTI Internal View 페이지 테스트"""
    
    SCENARIO_NAME = "자동검증 5: Career MTI Internal View"
    SCREENSHOT_FILENAME = "screenshot_career_mti_internal_view.png"
    PAGE_PATH = "/mti/internal"
    
    async def run(self) -> bool:
        """테스트를 실행합니다."""
        print(f"🚀 {self.SCENARIO_NAME} 시작")
        
        try:
            # 1. Career Recommend 페이지로 이동
            if not await self.mysuni_page.goto_page(self.PAGE_PATH):
                return False
            
            # 2. 페이지 로딩 대기
            await self.mysuni_page.wait_for_page_loaded()
            
            # 3. 스크린샷 캡처
            screenshot_path = await self.take_screenshot(self.SCREENSHOT_FILENAME)
            
            # 4. LLM으로 화면 검증
            result, llm_response = await self.validate_with_llm(
                screenshot_path,
                validation_mode="strict"
            )
            
            # 5. 비정상 감지 시 Slack 알림
            if result == "비정상":
                self.notify_failure(
                    self.SCENARIO_NAME, 
                    llm_response, 
                    screenshot_path
                )
                return False
            
            print(f"✅ {self.SCENARIO_NAME} 완료 - 결과: {result}")
            return True
            
        except Exception as e:
            print(f"❌ {self.SCENARIO_NAME} 실패: {e}")
            return False
