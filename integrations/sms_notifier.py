"""
SMS 알림 전송 모듈
점검 결과 Fail 시 SMS 발송 API를 호출합니다.
"""

import urllib.request
import urllib.error
from typing import Dict, Any, Optional


class SmsNotifier:
    """SMS 알림 전송 클라이언트"""

    DEFAULT_API_URL = (
        "https://mysuni.sk.com/api/notification/public/notifications"
        "?notificationId=CareerPlaywright-FAIL"
    )

    def __init__(self, config: Dict[str, Any], proxy_url: Optional[str] = None):
        """
        Args:
            config:
                - enabled: SMS 발송 활성화 여부 (bool)
                - api_url: SMS API 엔드포인트 URL (선택, 기본값 사용)
                - timeout: 요청 타임아웃(초, 기본 10)
            proxy_url: 프록시 URL (선택)
        """
        self.enabled: bool = bool(config.get("enabled", False))
        self.api_url: str = config.get("api_url", self.DEFAULT_API_URL).strip()
        self.timeout: int = int(config.get("timeout", 10))
        self.proxy_url: Optional[str] = proxy_url

        if self.enabled and proxy_url:
            print(f"ℹ️ SmsNotifier uses proxy: {proxy_url}")

    def _build_opener(self) -> urllib.request.OpenerDirector:
        if self.proxy_url:
            proxy_handler = urllib.request.ProxyHandler({
                "http": self.proxy_url,
                "https": self.proxy_url,
            })
            return urllib.request.build_opener(proxy_handler)
        return urllib.request.build_opener()

    def send_fail_alert(self) -> bool:
        """
        Fail 판정 시 SMS API를 GET으로 호출합니다.

        Returns:
            bool: 호출 성공 여부
        """
        if not self.enabled:
            print("ℹ️ SMS 알림 비활성화 상태 - 발송 생략")
            return False

        print(f"📱 SMS 알림 발송 시도: {self.api_url}")
        try:
            req = urllib.request.Request(self.api_url, method="GET")
            opener = self._build_opener()
            with opener.open(req, timeout=self.timeout) as response:
                status = response.status
                body = response.read().decode("utf-8", errors="replace")
                if 200 <= status < 300:
                    print(f"✅ SMS 발송 완료 (HTTP {status})")
                    return True
                else:
                    print(f"⚠️ SMS API 응답 비정상: HTTP {status} / {body[:200]}")
                    return False
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"❌ SMS API HTTP 오류: {e.code} {e.reason} / {body[:200]}")
            return False
        except urllib.error.URLError as e:
            print(f"❌ SMS API 연결 오류: {e.reason}")
            return False
        except Exception as e:
            print(f"❌ SMS 발송 중 예외: {e}")
            return False
