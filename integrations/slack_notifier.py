"""
Slack 알림 전송 모듈
채널 또는 DM으로 텍스트 메시지와 파일을 전송합니다.
"""

import time
from typing import Dict, Optional
from pathlib import Path
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackNotifier:
    """Slack 알림 전송 클라이언트"""
    
    def __init__(self, config: Dict[str, str], proxy_url: Optional[str] = None):
        """
        Args:
            config: Slack 설정
                - bot_token: Slack 봇 토큰
                - channel_id: 채널 ID (선택, 최우선)
                - channel_name: 채널명 (선택, 예: #career-qa-noti)
                - dm_user_id: DM 대상 사용자 ID (선택)
                - dm_email: DM 대상 이메일 (선택)
                - retry_attempts: 재시도 횟수
                - retry_delay: 재시도 대기 시간(초)
            proxy_url: 프록시 URL (선택)
        """
        self.config = config
        self.client = WebClient(
            token=config["bot_token"],
            proxy=proxy_url or None,
            timeout=30
        )
        self.retry_attempts = config.get("retry_attempts", 3)
        self.retry_delay = config.get("retry_delay", 2)
        
        if proxy_url:
            print(f"ℹ️ Slack Client uses proxy: {proxy_url}")
        
        # 전송 대상 캐시 (채널 ID 또는 DM 채널 ID)
        self._channel_id: Optional[str] = None
        self._dm_channel_id: Optional[str] = None

    def _has_channel_target(self) -> bool:
        """채널 대상 설정 여부를 반환합니다."""
        return bool((self.config.get("channel_id") or "").strip() or (self.config.get("channel_name") or "").strip())

    def _is_send_dm_also_enabled(self) -> bool:
        """채널 전송 시 DM 동시 전송 옵션 여부를 반환합니다."""
        return bool(self.config.get("send_dm_also", False))

    def _resolve_channel_id_from_name(self, channel_name: str) -> Optional[str]:
        """채널명으로 채널 ID를 조회합니다. 실패 시 None을 반환합니다."""
        normalized = channel_name.strip()
        if normalized.startswith("#"):
            normalized = normalized[1:]

        try:
            cursor = None
            while True:
                resp = self.client.conversations_list(
                    types="public_channel,private_channel",
                    limit=1000,
                    cursor=cursor,
                    exclude_archived=True,
                )
                for channel in resp.get("channels", []):
                    if channel.get("name") == normalized:
                        return channel.get("id")

                cursor = resp.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break

        except SlackApiError as e:
            print(f"⚠️ 채널명 조회 실패: {e.response.get('error', str(e))}")
        except Exception as e:
            print(f"⚠️ 채널명 조회 중 예외: {e}")

        return None
    
    def _resolve_dm_channel_id(self) -> Optional[str]:
        """
        DM 채널 ID를 조회합니다.
        dm_user_id가 없으면 dm_email로 조회한 뒤 DM 채널을 엽니다.
        """
        if self._dm_channel_id:
            return self._dm_channel_id

        try:
            user_id = (self.config.get("dm_user_id") or "").strip()

            if not user_id and self.config.get("dm_email"):
                resp = self.client.users_lookupByEmail(email=self.config["dm_email"])
                user_id = resp["user"]["id"]
                print(f"✅ 이메일로 사용자 ID 조회 성공: {user_id}")

            if not user_id:
                return None

            open_res = self.client.conversations_open(users=user_id)
            self._dm_channel_id = open_res["channel"]["id"]
            print(f"✅ DM 채널 ID: {self._dm_channel_id}")
            return self._dm_channel_id

        except SlackApiError as e:
            print(f"❌ Slack DM 채널 열기 실패: {e.response.get('error', str(e))}")
            return None
        except Exception as e:
            print(f"❌ Slack DM 채널 식별 실패: {e}")
            return None

    def _resolve_target_channel_id(self) -> Optional[str]:
        """
        기본 전송 대상 채널 ID를 조회합니다.
        우선순위: channel_id > channel_name > DM(dm_user_id/dm_email)
        Returns: 채널 ID 또는 채널명(조회 실패 시) (실패 시 None)
        """
        if self._channel_id:
            return self._channel_id
        
        try:
            configured_channel_id = (self.config.get("channel_id") or "").strip()
            if configured_channel_id:
                self._channel_id = configured_channel_id
                print(f"✅ Slack 채널 ID 사용: {self._channel_id}")
                return self._channel_id

            configured_channel_name = (self.config.get("channel_name") or "").strip()
            if configured_channel_name:
                if configured_channel_name.startswith("C"):
                    self._channel_id = configured_channel_name
                else:
                    resolved = self._resolve_channel_id_from_name(configured_channel_name)
                    self._channel_id = resolved or configured_channel_name
                print(f"✅ Slack 채널 대상 사용: {self._channel_id}")
                return self._channel_id

            dm_channel_id = self._resolve_dm_channel_id()
            if not dm_channel_id:
                raise RuntimeError(
                    "Slack 대상이 없습니다. channel_id/channel_name 또는 dm_user_id/dm_email을 설정하세요."
                )

            self._channel_id = dm_channel_id
            print(f"✅ DM 채널 ID: {self._channel_id}")
            
            return self._channel_id
            
        except SlackApiError as e:
            print(f"❌ Slack 채널 열기 실패: {e.response.get('error', str(e))}")
            return None
        except Exception as e:
            print(f"❌ Slack 채널 식별 실패 (네트워크/프록시/방화벽 가능성): {e}")
            print("   - 회사망이라면 HTTPS_PROXY/HTTP_PROXY 환경변수 설정을 확인하세요.")
            print("   - 사내 SSL 검증이 필요한 경우 REQUESTS_CA_BUNDLE 또는 "
                  "SSL_CERT_FILE 설정을 확인하세요.")
            return None

    def _resolve_target_channel_ids(self) -> list[str]:
        """실제 전송 대상 목록을 계산합니다. (기본 대상 + 옵션 DM 동시 전송)"""
        targets: list[str] = []

        primary_target = self._resolve_target_channel_id()
        if primary_target:
            targets.append(primary_target)

        # 채널 전송이 기본 대상일 때만 DM 동시 전송 옵션을 적용한다.
        if self._has_channel_target() and self._is_send_dm_also_enabled():
            dm_target = self._resolve_dm_channel_id()
            if dm_target and dm_target not in targets:
                targets.append(dm_target)

        return targets

    def _send_text_to_channel(self, channel_id: str, message: str) -> bool:
        """단일 대상에 텍스트를 전송합니다."""
        for attempt in range(self.retry_attempts):
            try:
                self.client.chat_postMessage(channel=channel_id, text=message)
                return True
            except Exception:
                if attempt == self.retry_attempts - 1:
                    raise
                time.sleep(self.retry_delay * (attempt + 1))
        return False

    def _send_file_to_channel(self, channel_id: str, message: str, filepath: Path) -> bool:
        """단일 대상에 파일을 전송합니다."""
        for attempt in range(self.retry_attempts):
            try:
                self.client.files_upload_v2(
                    channel=channel_id,
                    initial_comment=message,
                    file=str(filepath),
                )
                return True
            except Exception:
                if attempt == self.retry_attempts - 1:
                    raise
                time.sleep(self.retry_delay * (attempt + 1))
        return False
    
    def send_text(self, message: str) -> bool:
        """
        텍스트 메시지를 Slack 대상으로 전송합니다.
        Args: message: 전송할 메시지
        Returns: 전송 성공 여부
        """
        targets = self._resolve_target_channel_ids()
        if not targets:
            print("❌ Slack 텍스트 전송 실패: 대상 채널이 없습니다.")
            return False

        all_success = True
        for channel_id in targets:
            try:
                self._send_text_to_channel(channel_id, message)
                print(f"✅ Slack 전송 성공 (텍스트): {channel_id}")
            except SlackApiError as e:
                all_success = False
                print(f"❌ Slack 텍스트 전송 실패 ({channel_id}): {e.response.get('error', str(e))}")
            except Exception as e:
                all_success = False
                print(f"❌ Slack 텍스트 처리 중 예외 ({channel_id}): {e}")

        return all_success
    
    def send_file(self, message: str, filepath: Path) -> bool:
        """
        파일과 함께 메시지를 Slack 대상으로 전송합니다.
        Args:
            message: 파일과 함께 보낼 메시지
            filepath: 전송할 파일 경로
        Returns: 전송 성공 여부
        """
        targets = self._resolve_target_channel_ids()
        if not targets:
            print("❌ Slack 파일 전송 실패: 대상 채널이 없습니다.")
            return False

        all_success = True
        for channel_id in targets:
            try:
                self._send_file_to_channel(channel_id, message, filepath)
                print(f"✅ Slack 전송 성공 (파일): {channel_id}")
            except SlackApiError as e:
                all_success = False
                print(f"❌ Slack 파일 전송 실패 ({channel_id}): {e.response.get('error', str(e))}")
            except Exception as e:
                all_success = False
                print(f"❌ Slack 파일 전송 예외 ({channel_id}): {e}")

        return all_success
    
    def send_failure_notification(
        self, 
        scenario_name: str, 
        llm_response: str, 
        screenshot_path: Path
    ) -> bool:
        """
        테스트 실패 알림을 전송합니다.
        Args:
            scenario_name: 테스트 시나리오 이름
            llm_response: LLM 판별 응답
            screenshot_path: 스크린샷 파일 경로
        Returns: 전송 성공 여부
        """
        text_message = (
            f"🚨 [자동검증] 비정상 화면 감지\n"
            f"시나리오: {scenario_name}\n"
            f"LLM 판별: {llm_response}"
        )
        
        # 텍스트 메시지 전송
        self.send_text(text_message)
        
        # 스크린샷 전송
        file_message = f"[{scenario_name}] 비정상 화면 캡처\nLLM 응답: {llm_response}"
        return self.send_file(file_message, screenshot_path)

    def send_failure_item_notification(
        self,
        *,
        scenario_key: str,
        item_id: int,
        item_name: str,
        action_type: str,
        result: str,
        summary: str,
        llm_response: str,
        screenshot_path: Path,
    ) -> bool:
        """항목 단위 실패/판단불가 알림을 요청 포맷에 맞춰 전송합니다."""
        service_name_map = {
            "career_profile": "Career Profile",
            "career_recommend": "Career Recommend",
            "career_mypick": "Career My Pick",
            "career_1on1": "Career Coach 1on1",
            "career_myprogress": "Career Coach My Progress",
        }
        service_name = service_name_map.get(scenario_key, scenario_key)
        detection_label = "판정불가" if result in {"판단불가", "판정불가"} else "실패"

        # 파일 업로드의 initial_comment에 본문을 담아 단일 메시지로 전송한다.
        single_message = (
            f"❌ [{service_name} 자동점검 결과] {detection_label} 항목 감지\n\n"
            f"• *시나리오*: {scenario_key}\n"
            f"• *항목 ID*: {item_id}\n"
            f"• *항목명*: {item_name}\n"
            f"• *Action Type*: {action_type}\n"
            f"• *판정 결과*: {result}\n\n"
            f"• *요약 근거*:\n"
            f"   - {summary}"
        )

        return self.send_file(single_message, screenshot_path)
