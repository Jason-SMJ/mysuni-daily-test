"""
설정 관리 모듈
config.yaml과 .env 파일을 로드하고 관리합니다.
    - load_yaml_config(): config.yaml 읽기 (인코딩 처리)
    - get_azure_config(): Azure OpenAI 설정 반환
    - get_slack_config(): Slack 설정 반환
    - get_mysuni_credentials(): MySuni 로그인 정보 반환
    - get_browser_config(): 브라우저 설정 반환
    - get_test_pages(): 테스트 페이지 URL 반환
    - get_proxy_url(): 프록시 URL 반환  
"""

import os
from typing import Dict, Any, List
import yaml
from dotenv import load_dotenv


class Settings:
    """애플리케이션 설정을 관리하는 클래스"""

    @staticmethod
    def _to_bool(value: Any, default: bool = False) -> bool:
        """다양한 입력 값을 bool로 정규화합니다."""
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "y", "on"}:
            return True
        if text in {"0", "false", "no", "n", "off"}:
            return False
        return default
    
    def __init__(self, config_path: str = "config/config.yaml"):
        load_dotenv(override=True)
        self.config = self._load_yaml_config(config_path)
    
    def _load_yaml_config(self, path: str) -> Dict[str, Any]:
        encodings = ["utf-8", "utf-8-sig", "cp949"]
        for encoding in encodings:
            try:
                with open(path, "r", encoding=encoding) as f:
                    return yaml.safe_load(f)
            except UnicodeDecodeError:
                continue
            except FileNotFoundError:
                raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {path}")
        raise UnicodeDecodeError("utf-8", b"", 0, 1, f"파일을 읽을 수 없습니다: {path}")
    
    def get_azure_config(self) -> Dict[str, str]:
        azure_cfg = self.config.get("azure", {}).get("openai", {})
        return {
            "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", "") or azure_cfg.get("endpoint", ""),
            "api_key": os.getenv("AZURE_OPENAI_KEY", "") or azure_cfg.get("api_key", ""),
            "api_version": azure_cfg.get("api_version", "2024-05-01-preview"),
            "deployment": os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "") or azure_cfg.get("vision_deployment", "gpt-4-vision")
        }
    
    def get_slack_config(self) -> Dict[str, str]:
        slack_cfg = self.config.get("slack", {})
        send_dm_also_raw = os.getenv("SLACK_SEND_DM_ALSO", slack_cfg.get("send_dm_also", False))
        return {
            "bot_token": slack_cfg.get("bot_token", "") or os.getenv("SLACK_BOT_TOKEN", ""),
            "channel_id": slack_cfg.get("channel_id", "") or os.getenv("SLACK_CHANNEL_ID", ""),
            "channel_name": slack_cfg.get("channel_name", "") or os.getenv("SLACK_CHANNEL_NAME", ""),
            "dm_user_id": slack_cfg.get("dm_user_id", "") or os.getenv("SLACK_DM_USER_ID", ""),
            "dm_email": slack_cfg.get("dm_email", "") or os.getenv("SLACK_DM_EMAIL", ""),
            "send_dm_also": self._to_bool(send_dm_also_raw, default=False),
            "retry_attempts": slack_cfg.get("retry_attempts", 3),
            "retry_delay": slack_cfg.get("retry_delay", 2)
        }
    
    def get_mysuni_credentials(self) -> Dict[str, str]:
        mysuni_cfg = self.config.get("mysuni", {})
        return {
            "base_url": mysuni_cfg.get("base_url", "https://mysuni.sk.com/"),
            "career_url": mysuni_cfg.get("career_url", "https://career.mysuni.sk.com/"),
            "id": os.getenv("MYSUNI_ID", ""),
            "password": os.getenv("MYSUNI_PWD", "")
        }
    
    def get_browser_config(self) -> Dict[str, Any]:
        browser_cfg = self.config.get("browser", {})
        # BROWSER_HEADLESS 환경변수로 override 가능 (Docker 환경에서 true로 설정)
        headless_env = os.getenv("BROWSER_HEADLESS")
        if headless_env is not None:
            headless = self._to_bool(headless_env, default=False)
        else:
            headless = browser_cfg.get("headless", False)
        return {
            "headless": headless,
            "viewport": browser_cfg.get("viewport", {"width": 1280, "height": 1024}),
            "timeout": browser_cfg.get("timeout", 30000),
            "download_dir": browser_cfg.get("download_dir", "downloads"),
            "mobile_device": browser_cfg.get("mobile_device", "iPhone 12"),
        }
    
    def get_test_pages(self) -> Dict[str, str]:
        test_cfg = self.config.get("test", {})
        return test_cfg.get("pages", {})

    def get_test_scenarios(self) -> List[Dict[str, Any]]:
        test_cfg = self.config.get("test", {})
        return test_cfg.get("scenarios", [])
    
    def get_sms_config(self) -> Dict[str, Any]:
        sms_cfg = self.config.get("sms", {})
        sms_enabled_env = os.getenv("SMS_ENABLED", "").strip()
        if sms_enabled_env:
            enabled = self._to_bool(sms_enabled_env)
        else:
            enabled = self._to_bool(sms_cfg.get("enabled", True))
        return {
            "enabled": enabled,
            "api_url": (
                os.getenv("SMS_API_URL", "")
                or sms_cfg.get("api_url", "")
            ),
            "timeout": int(sms_cfg.get("timeout", 10)),
        }

    def get_proxy_url(self) -> str:
        return (os.getenv("HTTPS_PROXY", "") or os.getenv("https_proxy", "") 
                or os.getenv("HTTP_PROXY", "") or os.getenv("http_proxy", ""))
