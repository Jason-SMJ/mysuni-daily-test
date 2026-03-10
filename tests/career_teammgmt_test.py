"""
자동검증 9: Career Team Management 페이지 테스트
"""

from tests.base_test import BaseTest


class CareerTeamManagementTestScenario(BaseTest):
    SCENARIO_NAME = "자동검증 9: Career Team Management"
    SCREENSHOT_FILENAME = "screenshot_career_team_management.png"
    PAGE_PATH = "/career/team/management"
    
    async def run(self) -> bool:
        print(f"🚀 {self.SCENARIO_NAME} 시작")
        try:
            # 1. Career Profile 페이지로 이동
            if not await self.mysuni_page.goto_page(self.PAGE_PATH):
                return False
            
            # 2. 페이지 로딩 대기
            await self.mysuni_page.wait_for_page_loaded()

            # 3. 스크린샷 캡처
            screenshot_path = await self.take_screenshot(self.SCREENSHOT_FILENAME)
            
            # 4. LLM으로 화면 검증
            result, llm_response = await self.validate_with_llm(screenshot_path, "strict")
            
            # 5. 비정상 감지 시 Slack 알림
            if result == "비정상":
                self.notify_failure(self.SCENARIO_NAME, llm_response, screenshot_path)
                return False
            
            print(f"✅ {self.SCENARIO_NAME} 완료 - {result}")
            return True
        
        except Exception as e:
            print(f"❌ {self.SCENARIO_NAME} 실패: {e}")
            return False
