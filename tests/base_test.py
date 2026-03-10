"""
테스트 베이스 클래스
모든 테스트 시나리오가 상속받는 기본 클래스입니다.
"""

from typing import Literal
from pathlib import Path
from playwright.async_api import Page

from core.browser import MySuniPage
from core.screenshot import ScreenshotManager
from integrations.azure_openai import AzureVisionClient
from integrations.slack_notifier import SlackNotifier


class BaseTest:
    """테스트 시나리오의 기본 클래스"""
    
    def __init__(
        self,
        page: Page,
        mysuni_page: MySuniPage,
        screenshot_manager: ScreenshotManager,
        vision_client: AzureVisionClient,
        slack_notifier: SlackNotifier
    ):
        """
        Args:
            page: Playwright Page 객체
            mysuni_page: MySuni 페이지 헬퍼
            screenshot_manager: 스크린샷 관리자
            vision_client: Azure Vision 클라이언트
            slack_notifier: Slack 알림 전송자
        """
        self.page = page
        self.mysuni_page = mysuni_page
        self.screenshot_manager = screenshot_manager
        self.vision_client = vision_client
        self.slack_notifier = slack_notifier
    
    async def take_screenshot(self, filename: str) -> Path:
        """
        현재 페이지의 전체 스크린샷을 캡처합니다.
        Args: filename: 저장할 파일명
        Returns: 저장된 파일 경로
        """
        return await self.screenshot_manager.capture_full_page(self.page, filename)
    
    async def validate_with_llm(
        self,
        screenshot_path: Path,
        validation_mode: Literal["lenient", "strict"] = "strict",
        custom_prompt: str | None = None,
        reference_image_path: Path | None = None,
    ) -> tuple[str, str]:
        """
        스크린샷을 LLM으로 검증합니다.
        Args:
            screenshot_path: 검증할 스크린샷 경로
            validation_mode: 검증 모드
            custom_prompt: 체크리스트 항목별 커스텀 프롬프트
            reference_image_path: 비교용 기준 이미지 경로
        Returns: (판정결과, LLM응답) 튜플   
        """
        data_url = self.screenshot_manager.get_data_url(screenshot_path)
        reference_data_url = (
            self.screenshot_manager.get_data_url(reference_image_path)
            if reference_image_path and reference_image_path.exists()
            else None
        )
        return self.vision_client.validate_screenshot(
            data_url,
            validation_mode=validation_mode,
            custom_prompt=custom_prompt,
            reference_image_data_url=reference_data_url,
        )
    
    def notify_failure(
        self, 
        scenario_name: str, 
        llm_response: str, 
        screenshot_path: Path
    ):
        """
        테스트 실패를 Slack으로 알립니다.
        Args:
            scenario_name: 시나리오 이름
            llm_response: LLM 응답
            screenshot_path: 스크린샷 경로
        """
        self.slack_notifier.send_failure_notification(
            scenario_name, 
            llm_response, 
            screenshot_path
        )
    
    async def run(self) -> bool:
        """
        테스트를 실행합니다. 서브클래스에서 구현해야 합니다.
        Returns: 테스트 성공 여부
        """
        raise NotImplementedError("서브클래스에서 run() 메서드를 구현해야 합니다.")
