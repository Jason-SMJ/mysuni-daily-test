"""
자동검증 5: Career Recommend 페이지 테스트
커리어 추천 페이지의 AI 기능이 정상 작동하는지 검증합니다.
"""

from pathlib import Path

from tests.base_test import BaseTest


class CareerRecommendTestScenario(BaseTest):
    """Career Recommend 페이지 테스트"""
    
    SERVICE_KEY = "career_recommend"
    SCENARIO_NAME = "자동검증 5: Career Recommend"
    SCREENSHOT_FILENAME = "screenshot_career_recommend.png"
    PAGE_PATH = "/suni-main/career?page=/career/recommend"

    def _resolve_reference_image(self) -> Path | None:
        path = Path("baselines") / self.SERVICE_KEY / self.SCREENSHOT_FILENAME
        return path if path.exists() else None
    
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
            screenshot_path = await self.take_screenshot(
                f"{self.SERVICE_KEY}/{self.SCREENSHOT_FILENAME}"
            )
            
            # 4. LLM으로 화면 검증
            result, llm_response = await self.validate_with_llm(
                screenshot_path,
                validation_mode="strict",
                reference_image_path=self._resolve_reference_image(),
            )
            self.record_item_result(
                scenario_key=self.SERVICE_KEY,
                item_id=1,
                item_name="Career Recommend 메인 화면 점검",
                action_type="navigate",
                result=result,
                llm_response=llm_response,
                screenshot_path=screenshot_path,
            )
            
            # 5. 비정상/판단불가 감지 시 Slack 알림
            if result != "정상":
                self.notify_failure_item(
                    scenario_key=self.SERVICE_KEY,
                    item_id=1,
                    item_name="Career Recommend 메인 화면 점검",
                    action_type="navigate",
                    result=result,
                    llm_response=llm_response,
                    screenshot_path=screenshot_path,
                )
                return False
            
            print(f"✅ {self.SCENARIO_NAME} 완료 - 결과: {result}")
            return True
            
        except Exception as e:
            print(f"❌ {self.SCENARIO_NAME} 실패: {e}")
            return False
