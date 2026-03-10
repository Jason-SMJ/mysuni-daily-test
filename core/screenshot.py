"""
스크린샷 캡처 및 관리 모듈
"""

import base64
from pathlib import Path
from typing import Optional
from playwright.async_api import Page, Locator


class ScreenshotManager:
    """스크린샷 캡처 및 인코딩을 담당하는 클래스"""
    
    def __init__(self, output_dir: str = "screenshots"):
        """
        Args: output_dir: 스크린샷을 저장할 디렉토리
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def capture_element(
        self, 
        locator: Locator, 
        filename: str,
        fallback_page: Optional[Page] = None,
        ensure_content: bool = False,
    ) -> Path:
        """
        특정 요소의 스크린샷을 캡처합니다.
        Args:
            locator: 캡처할 요소의 Locator
            filename: 저장할 파일명 (확장자 포함)
            fallback_page: 요소 캡처 실패 시 전체 페이지 캡처에 사용할 Page 객체
        Returns:저장된 파일의 경로
        """
        filepath = self.output_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            await locator.scroll_into_view_if_needed()
            await locator.wait_for(state="visible", timeout=5000)

            if ensure_content:
                # 빈 흰 화면 캡처를 줄이기 위해 실제 콘텐츠 렌더를 짧은 폴링으로 확인한다.
                content_ready = False
                for _ in range(8):
                    try:
                        content_ready = bool(
                            await locator.evaluate(
                                """
                                (el) => {
                                  const text = (el.innerText || el.textContent || '').trim();
                                  const hasField = el.querySelectorAll('input, textarea, select, button').length > 0;
                                  const rect = el.getBoundingClientRect();
                                  return rect.width > 0 && rect.height > 0 && (text.length >= 4 || hasField);
                                }
                                """
                            )
                        )
                    except Exception:
                        content_ready = False

                    if content_ready:
                        break
                    await locator.page.wait_for_timeout(250)

                if not content_ready:
                    raise RuntimeError("요소 콘텐츠 렌더 확인 실패")

            await locator.screenshot(path=str(filepath), animations="disabled")
            print(f"📸 스크린샷 저장 완료: {filepath}")
        except Exception as e:
            if fallback_page:
                print(f"⚠️ 요소 캡처 실패, 전체 페이지 캡처로 대체: {e}")
                await fallback_page.screenshot(path=str(filepath), full_page=True)
            else:
                raise e
        
        return filepath
    
    async def capture_full_page(
        self, 
        page: Page, 
        filename: str
    ) -> Path:
        """
        전체 페이지 스크린샷을 캡처합니다.
        Args:
            page: 캡처할 Page 객체
            filename: 저장할 파일명 (확장자 포함)
        Returns: 저장된 파일의 경로
        """
        filepath = self.output_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(filepath), full_page=True)
        print(f"📸 전체 페이지 스크린샷 저장: {filepath}")
        return filepath
    
    @staticmethod
    def encode_to_base64(filepath: Path) -> str:
        """
        이미지 파일을 base64로 인코딩합니다.
        Args: filepath: 이미지 파일 경로
        Returns: base64 인코딩된 문자열
        """
        with open(filepath, "rb") as img:
            return base64.b64encode(img.read()).decode("utf-8")
    
    def get_data_url(self, filepath: Path) -> str:
        """
        이미지 파일을 data URL로 변환합니다.
        Args: filepath: 이미지 파일 경로
        Returns: data:image/png;base64,... 형식의 URL
        """
        b64_data = self.encode_to_base64(filepath)
        return f"data:image/png;base64,{b64_data}"
    
