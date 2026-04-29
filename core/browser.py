"""
Playwright 브라우저 관리 모듈 - 다운로드 기능 포함
"""

from typing import Optional, Dict
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page, Playwright, Download


class BrowserManager:
    """Playwright 브라우저 생성 및 관리"""
    
    def __init__(self, headless: bool = False, viewport: Optional[Dict[str, int]] = None, download_dir: str = "downloads"):
        self.headless = headless
        self.viewport = viewport or {"width": 1280, "height": 1024}
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
    
    async def __aenter__(self):
        await self.launch()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def launch(self) -> Browser:
        self.playwright = await async_playwright().start()
        args = []
        if self.headless:
            # Docker/컨테이너 환경(Display 없음)에서 필수 옵션
            args = ["--no-sandbox", "--disable-dev-shm-usage"]
        self.browser = await self.playwright.chromium.launch(headless=self.headless, args=args)
        return self.browser
    
    async def new_page(self) -> Page:
        if not self.browser:
            await self.launch()
        context = await self.browser.new_context(viewport=self.viewport, accept_downloads=True)
        page = await context.new_page()
        return page

    async def new_mobile_page(
        self,
        device_name: str = "iPhone 12",
        user_agent: str | None = None,
    ) -> Page:
        """모바일 페이지 생성.

        user_agent가 지정되면 device 에뮬레이션 없이 해당 UA만 설정한다.
        """
        if not self.browser:
            await self.launch()
        if user_agent:
            context = await self.browser.new_context(
                user_agent=user_agent,
                viewport=self.viewport,
                accept_downloads=True,
            )
        else:
            device = self.playwright.devices[device_name]
            context = await self.browser.new_context(**device, accept_downloads=True)
        return await context.new_page()

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


class MySuniPage:
    """MySuni 웹사이트 전용 페이지 헬퍼 - 다운로드 기능 포함"""
    
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip('/')
    
    async def login(self, username: str, password: str) -> bool:
        try:
            await self.page.goto(self.base_url, wait_until="networkidle")
            print(f"🌐 현재 URL: {self.page.url}")
            await self.page.screenshot(path="screenshots/debug/login_page.png")
            print("📸 로그인 페이지 스크린샷 저장: screenshots/debug/login_page.png")
            await self.page.wait_for_selector('#user-login-id', timeout=30000)
            await self.page.fill('#user-login-id', username)
            await self.page.wait_for_selector('#user-password', timeout=30000)
            await self.page.fill('#user-password', password)
            await self.page.get_by_role("button", name="로그인").click()
            await self.page.wait_for_timeout(10000)
            print("✅ 로그인 성공")
            return True
        except Exception as e:
            print(f"❌ 로그인 실패: {e}")
            return False
    
    async def goto_page(self, page_path: str) -> bool:
        try:
            url = f"{self.base_url}{page_path}"
            await self.page.goto(url, wait_until="networkidle")
            print(f"✅ 페이지 이동: {url}")
            await self.page.wait_for_timeout(3000)
            return True
        except Exception as e:
            print(f"❌ 페이지 이동 실패: {e}")
            return False
    
    
    async def click_download_button(self, selector: str = "button:has-text('다운로드'), a:has-text('다운로드'), [download]", timeout: int = 30000) -> Optional[Path]:
        """다운로드 버튼 클릭 및 파일 다운로드 처리"""
        try:
            async with self.page.expect_download(timeout=timeout) as download_info:
                button = self.page.locator(selector).first
                await button.scroll_into_view_if_needed()
                await button.click()
                print("✅ 다운로드 버튼 클릭")
            
            download: Download = await download_info.value
            filename = download.suggested_filename
            filepath = Path("downloads") / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            await download.save_as(filepath)
            print(f"📥 다운로드 완료: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ 다운로드 실패: {e}")
            return None
    
    async def wait_for_page_loaded(self, timeout: int = 10000):
        try:
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception:
            await self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
