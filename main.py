"""
MySuni 자동 점검 메인 실행 파일
Pilot 1단계: Career Profile 체크리스트 검증 우선 실행
"""

import asyncio
import argparse
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from typing import Callable

KST = timezone(timedelta(hours=9))
from config.settings import Settings
from core.browser import BrowserManager, MySuniPage
from core.screenshot import ScreenshotManager
from integrations.azure_openai import AzureVisionClient
from integrations.slack_notifier import SlackNotifier
from integrations.sms_notifier import SmsNotifier

# Career 시나리오
from tests.career_test import (
    CareerProfileTestScenario,
    CareerExtendedTestScenario,
    CareerRecommendTestScenario,
    CareerMyPickTestScenario,
    Career1on1TestScenario,
    CareerMyProgressTestScenario,
)

# LMS / One_ID 시나리오
from tests.lms_pc_test import LmsPcTestScenario
from tests.lms_ai_test import LmsAiTestScenario
from tests.lms_mobile_test import LmsMobileTestScenario
from tests.one_id_test import OneIdTestScenario


@dataclass
class ScenarioPlan:
    key: str
    name: str
    enabled: bool
    skip_reason: str
    factory: Callable[[], object]
    base_url: str | None = None  # None이면 현재 base_url 유지

def parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MySuni 자동 점검 실행")
    parser.add_argument(
        "--scenario",
        type=str,
        choices=[
            "career_profile",
            "career_recommend",
            "career_mypick",
            "career_1on1",
            "career_myprogress",
            "career_extended",
            "lms_pc",
            "lms_ai",
            "lms_mobile",
            "one_id",
        ],
        help="특정 시나리오만 실행합니다.",
    )
    parser.add_argument(
        "--item",
        type=int,
        help="career_profile 체크리스트의 특정 항목(1-based)만 실행합니다.",
    )
    return parser.parse_args()


async def main(selected_scenario: str | None = None, selected_item: int | None = None):
    """메인 실행 함수"""
    
    print("="*60)
    print("🚀 MySuni 일일점검 자동 검증 시작")
    print("="*60)
    
    # 1. 설정 로드
    print("\n📋 설정 로드 중...")
    settings = Settings()
    
    azure_config = settings.get_azure_config()
    slack_config = settings.get_slack_config()
    sms_config = settings.get_sms_config()
    mysuni_config = settings.get_mysuni_credentials()
    browser_config = settings.get_browser_config()
    proxy_url = settings.get_proxy_url()
    scenario_config = {
        item.get("name", ""): item for item in settings.get_test_scenarios()
    }

    # 환경변수 로딩 확인 출력
    def mask(v): return (str(v)[:4] + "****" + str(v)[-2:]) if v and len(str(v)) > 6 else ("****" if v else "(없음)")
    print("\n🔑 환경변수 로딩 확인:")
    print(f"  AZURE_OPENAI_KEY     : {mask(azure_config.get('api_key'))}")
    print(f"  AZURE_ENDPOINT       : {azure_config.get('endpoint', '(없음)')}")
    print(f"  AZURE_DEPLOYMENT     : {azure_config.get('vision_deployment', '(없음)')}")
    print(f"  SLACK_BOT_TOKEN      : {mask(slack_config.get('bot_token'))}")
    print(f"  SLACK_CHANNEL_ID     : {slack_config.get('channel_id') or '(없음)'}")
    print(f"  SLACK_CHANNEL_NAME   : {slack_config.get('channel_name') or '(없음)'}")
    print(f"  SLACK_DM_USER_ID     : {slack_config.get('dm_user_id') or '(없음)'}")
    print(f"  SLACK_DM_EMAIL       : {slack_config.get('dm_email') or '(없음)'}")
    print(f"  SLACK_SEND_DM_ALSO   : {slack_config.get('send_dm_also', False)}")
    print(f"  MYSUNI_ID            : {mysuni_config.get('id', '(없음)')}")
    print(f"  MYSUNI_PWD           : {mask(mysuni_config.get('password'))}")
    print(f"  HTTPS_PROXY          : {proxy_url or '(없음)'}")
    print(f"  BROWSER_HEADLESS     : {browser_config.get('headless', False)}")
    print(f"  SMS_ENABLED          : {sms_config.get('enabled', False)}")
    print(f"  SMS_API_URL          : {sms_config.get('api_url') or '(기본값 사용)'}")

    # 2. 클라이언트 초기화
    print("🔧 클라이언트 초기화 중...")
    vision_client = AzureVisionClient(azure_config)
    slack_notifier = SlackNotifier(slack_config, proxy_url)
    sms_notifier = SmsNotifier(sms_config, proxy_url)
    screenshot_manager = ScreenshotManager(output_dir="screenshots")
    
    # 3. 브라우저 시작 및 테스트 실행
    async with BrowserManager(
        headless=browser_config["headless"],
        viewport=browser_config["viewport"],
        download_dir=browser_config["download_dir"]
    ) as browser_manager:
        
        # 페이지 생성
        page = await browser_manager.new_page()
        mysuni_page = MySuniPage(page, mysuni_config["base_url"])

        # 모바일 에뮬레이션 페이지 (LMS_Mobile 전용)
        mobile_device = browser_config.get("mobile_device", "iPhone 12")
        mobile_page = await browser_manager.new_mobile_page(mobile_device)
        mobile_mysuni_page = MySuniPage(mobile_page, mysuni_config["base_url"])
        
        # 4. MySuni 로그인
        print("\n🔑 MySuni 로그인 중...")
        if not await mysuni_page.login(
            mysuni_config["id"], 
            mysuni_config["password"]
        ):
            print("❌ 로그인 실패")
            slack_notifier.send_text("❌ MySuni 로그인 실패")

            executed_at = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
            login_fail_summary = "\n".join(
                [
                    "[mySUNI 일일점검 결과 Summary]",
                    f"• *실행 일시*: {executed_at}",
                    "• *대상 시나리오*: 로그인 실패로 미진행",
                    "• *점검 결과*",
                    "   - 전체 : 성공 0 / 실패 1 / 판단불가 0 / 스킵 0",
                    "",
                    "• *❌ 실패 항목 목록*: ",
                    "1. common / item N/A / login / 비정상",
                    "   - 항목명: MySuni 로그인",
                    "   - 요약: 로그인 페이지 진입 또는 로그인 폼 탐색 실패",
                    "   - 스크린샷: N/A",
                    "",
                    "• *조치 우선순위*:",
                    "- 1순위: 계정/비밀번호 및 로그인 페이지 접근 상태 확인",
                    "- 2순위: 네트워크/프록시/로딩 지연 여부 확인",
                ]
            )
            slack_notifier.send_text(login_fail_summary)
            return
        
        print("✅ 로그인 성공")

        lms_base_url = mysuni_config["base_url"].rstrip("/")
        career_base_url = mysuni_config["career_url"].rstrip("/")

        # 로그인 이후 기본 base_url은 career_url로 전환 (기존 Career 시나리오 유지)
        mysuni_page.base_url = career_base_url
        print(f"🌐 테스트 URL 전환: {mysuni_page.base_url}")

        # 모바일 페이지도 LMS base_url로 설정
        mobile_mysuni_page.base_url = lms_base_url

        # 모바일 로그인
        print("📱 모바일 페이지 로그인 중...")
        await mobile_mysuni_page.login(mysuni_config["id"], mysuni_config["password"])

        # 5. 테스트 시나리오 계획 수립
        scenario_plans = [
            # ── LMS_PC ──────────────────────────────────────
            ScenarioPlan(
                key="lms_pc",
                name="LMS PC",
                enabled=scenario_config.get("lms_pc", {}).get("enabled", False),
                skip_reason=scenario_config.get("lms_pc", {}).get("skip_reason", "미활성화"),
                base_url=lms_base_url,
                factory=lambda: LmsPcTestScenario(
                    page, mysuni_page, screenshot_manager, vision_client, slack_notifier
                ),
            ),
            # ── LMS_AI ──────────────────────────────────────
            ScenarioPlan(
                key="lms_ai",
                name="LMS AI 학습도우미",
                enabled=scenario_config.get("lms_ai", {}).get("enabled", False),
                skip_reason=scenario_config.get("lms_ai", {}).get("skip_reason", "미활성화"),
                base_url=lms_base_url,
                factory=lambda: LmsAiTestScenario(
                    page, mysuni_page, screenshot_manager, vision_client, slack_notifier
                ),
            ),
            # ── LMS_Mobile ──────────────────────────────────
            ScenarioPlan(
                key="lms_mobile",
                name="LMS Mobile",
                enabled=scenario_config.get("lms_mobile", {}).get("enabled", False),
                skip_reason=scenario_config.get("lms_mobile", {}).get("skip_reason", "미활성화"),
                base_url=lms_base_url,
                factory=lambda: LmsMobileTestScenario(
                    mobile_page, mobile_mysuni_page, screenshot_manager, vision_client, slack_notifier
                ),
            ),
            # ── Career Profile (기존) ────────────────────────
            ScenarioPlan(
                key="career_profile",
                name="Pilot: Career Profile",
                enabled=scenario_config.get("career_profile", {}).get("enabled", True),
                skip_reason=scenario_config.get("career_profile", {}).get("skip_reason", ""),
                base_url=career_base_url,
                factory=lambda: CareerProfileTestScenario(
                    page,
                    mysuni_page,
                    screenshot_manager,
                    vision_client,
                    slack_notifier,
                    target_item_index=selected_item,
                ),
            ),
            # ── Career 확장 (추천·My Pick) ───────────────────
            ScenarioPlan(
                key="career_extended",
                name="Career 확장 (추천·My Pick)",
                enabled=scenario_config.get("career_extended", {}).get("enabled", False),
                skip_reason=scenario_config.get("career_extended", {}).get("skip_reason", "미활성화"),
                base_url=career_base_url,
                factory=lambda: CareerExtendedTestScenario(
                    page, mysuni_page, screenshot_manager, vision_client, slack_notifier
                ),
            ),
            # ── One_ID ──────────────────────────────────────
            ScenarioPlan(
                key="one_id",
                name="One_ID (일반사용자)",
                enabled=scenario_config.get("one_id", {}).get("enabled", False),
                skip_reason=scenario_config.get("one_id", {}).get("skip_reason", "미활성화"),
                base_url=lms_base_url,
                factory=lambda: OneIdTestScenario(
                    page, mysuni_page, screenshot_manager, vision_client, slack_notifier
                ),
            ),
            # ── 기존 단순 Career 시나리오 ─────────────────────
            ScenarioPlan(
                key="career_recommend",
                name="Career Recommend",
                enabled=scenario_config.get("career_recommend", {}).get("enabled", False),
                skip_reason=scenario_config.get("career_recommend", {}).get("skip_reason", "Pilot 1단계 범위 제외"),
                base_url=career_base_url,
                factory=lambda: CareerRecommendTestScenario(
                    page, mysuni_page, screenshot_manager, vision_client, slack_notifier
                ),
            ),
            ScenarioPlan(
                key="career_mypick",
                name="Career My Pick",
                enabled=scenario_config.get("career_mypick", {}).get("enabled", False),
                skip_reason=scenario_config.get("career_mypick", {}).get("skip_reason", "Pilot 1단계 범위 제외"),
                base_url=career_base_url,
                factory=lambda: CareerMyPickTestScenario(
                    page, mysuni_page, screenshot_manager, vision_client, slack_notifier
                ),
            ),
            ScenarioPlan(
                key="career_1on1",
                name="Career Coach 1on1",
                enabled=scenario_config.get("career_1on1", {}).get("enabled", False),
                skip_reason=scenario_config.get("career_1on1", {}).get("skip_reason", "Pilot 1단계 범위 제외"),
                base_url=career_base_url,
                factory=lambda: Career1on1TestScenario(
                    page, mysuni_page, screenshot_manager, vision_client, slack_notifier
                ),
            ),
            ScenarioPlan(
                key="career_myprogress",
                name="Career Coach My Progress",
                enabled=scenario_config.get("career_myprogress", {}).get("enabled", False),
                skip_reason=scenario_config.get("career_myprogress", {}).get("skip_reason", "Pilot 1단계 범위 제외"),
                base_url=career_base_url,
                factory=lambda: CareerMyProgressTestScenario(
                    page, mysuni_page, screenshot_manager, vision_client, slack_notifier
                ),
            ),
        ]

        if selected_scenario:
            scenario_plans = [plan for plan in scenario_plans if plan.key == selected_scenario]
            if not scenario_plans:
                print(f"❌ 알 수 없는 시나리오: {selected_scenario}")
                return
        
        # 6. 테스트 실행
        print("\n" + "="*60)
        print("🧪 테스트 시나리오 실행 중...")
        print("="*60)
        
        results = []
        total_abnormal_items = 0
        total_indeterminate_items = 0
        failure_items: list[dict[str, str | int]] = []
        _zero = {"success": 0, "failure": 0, "indeterminate": 0, "skip": 0}
        service_result_map: dict[str, dict[str, int]] = {
            "lms_pc": dict(_zero),
            "lms_ai": dict(_zero),
            "lms_mobile": dict(_zero),
            "career_profile": dict(_zero),
            "career_extended": dict(_zero),
            "one_id": dict(_zero),
            "career_recommend": dict(_zero),
            "career_mypick": dict(_zero),
            "career_1on1": dict(_zero),
            "career_myprogress": dict(_zero),
        }
        service_label_map = {
            "lms_pc": "LMS PC",
            "lms_ai": "LMS AI 학습도우미",
            "lms_mobile": "LMS Mobile",
            "career_profile": "Career Profile",
            "career_extended": "Career 확장 (추천·My Pick)",
            "one_id": "One_ID",
            "career_recommend": "Career Recommend",
            "career_mypick": "Career My Pick",
            "career_1on1": "Career Coach 1on1",
            "career_myprogress": "Career Coach My Progress",
        }

        for i, plan in enumerate(scenario_plans, 1):
            print(f"\n[{i}/{len(scenario_plans)}] {plan.name}")
            print("-" * 60)

            should_run = True if selected_scenario else plan.enabled
            if not should_run:
                print(f"⏭️ 스킵 - 사유: {plan.skip_reason}")
                results.append((plan.name, "SKIP", plan.skip_reason))
                service_result_map.setdefault(
                    plan.key,
                    {"success": 0, "failure": 0, "indeterminate": 0, "skip": 0},
                )["skip"] += 1
            else:
                # 시나리오별 base_url 전환 (LMS ↔ Career)
                if plan.base_url and plan.key not in ("lms_mobile",):
                    mysuni_page.base_url = plan.base_url
                    print(f"🌐 base_url 전환: {mysuni_page.base_url}")

                scenario = plan.factory()
                before_failure_count = len(failure_items)
                passed = await scenario.run()

                scenario_abnormal = 0
                scenario_indeterminate = 0
                scenario_success = 0
                if hasattr(scenario, "get_result_counts"):
                    counts = scenario.get_result_counts()
                    scenario_success = int(counts.get("정상", 0))
                    scenario_abnormal = int(counts.get("비정상", 0))
                    scenario_indeterminate = int(counts.get("판단불가", 0))
                    total_abnormal_items += scenario_abnormal
                    total_indeterminate_items += scenario_indeterminate

                service_metrics = service_result_map.setdefault(
                    plan.key,
                    {"success": 0, "failure": 0, "indeterminate": 0, "skip": 0},
                )
                service_metrics["success"] += scenario_success
                service_metrics["failure"] += scenario_abnormal
                service_metrics["indeterminate"] += scenario_indeterminate

                if hasattr(scenario, "get_failure_items"):
                    failure_items.extend(scenario.get_failure_items())

                # 항목 판정 전에 시나리오가 실패한 경우, 최종 요약에 원인을 남긴다.
                if not passed and len(failure_items) == before_failure_count:
                    failure_items.append(
                        {
                            "scenario": plan.key,
                            "item_id": 0,
                            "item_name": "시나리오 실행 실패",
                            "action_type": "none",
                            "result": "비정상",
                            "summary": "페이지 이동/예외로 항목 판정 전에 종료됨",
                        }
                    )
                    if scenario_abnormal == 0 and scenario_indeterminate == 0:
                        total_abnormal_items += 1
                        service_metrics["failure"] += 1

                results.append((plan.name, "PASS" if passed else "FAIL", ""))
            
            # 시나리오 간 대기
            if i < len(scenario_plans):
                await page.wait_for_timeout(2000)
        
        # 7. 결과 요약
        print("\n" + "="*60)
        print("📊 테스트 결과 요약")
        print("="*60)
        
        passed_count = 0
        failed_count = 0
        skipped_count = 0
        
        for name, status, reason in results:
            if status == "PASS":
                label = "✅ 성공"
                passed_count += 1
            elif status == "FAIL":
                label = "❌ 실패"
                failed_count += 1
            else:
                label = "⏭️ 스킵"
                skipped_count += 1

            if reason:
                print(f"{label} - {name} ({reason})")
            else:
                print(f"{label} - {name}")
        
        print("-" * 60)
        print(
            f"총 {len(results)}개 시나리오 중 성공: {passed_count}, "
            f"실패: {failed_count}, 스킵: {skipped_count}, "
            f"비정상 항목: {total_abnormal_items}, 판단불가 항목: {total_indeterminate_items}"
        )
        print("="*60)

        executed_at = datetime.now(KST).strftime("%Y-%m-%d %H:%M")

        total_success_items = sum(v["success"] for v in service_result_map.values())
        total_failure_items = sum(v["failure"] for v in service_result_map.values())
        total_indeterminate_items_from_services = sum(v["indeterminate"] for v in service_result_map.values())
        total_skips_from_services = sum(v["skip"] for v in service_result_map.values())

        summary_lines = [
            "[mySUNI 일일점검 결과 Summary]",
            f"• *실행 일시*: {executed_at}",
            f"• *대상 시나리오*: {len(scenario_plans)}개",
            "• *점검 결과*",
            (
                f"   - 전체 : 성공 {total_success_items} / 실패 {total_failure_items} / "
                f"판단불가 {total_indeterminate_items_from_services} / 스킵 {total_skips_from_services}"
            ),
        ]

        for plan in scenario_plans:
            metrics = service_result_map.get(
                plan.key,
                {"success": 0, "failure": 0, "indeterminate": 0, "skip": 0},
            )
            summary_lines.append(
                (
                    f"   - {service_label_map.get(plan.key, plan.name)} : "
                    f"성공 {metrics['success']} / 실패 {metrics['failure']} / "
                    f"판단불가 {metrics['indeterminate']} / 스킵 {metrics['skip']}"
                )
            )

        summary_lines.extend(["", "• *❌ 실패 항목 목록*:"])

        if failure_items:
            for idx, item in enumerate(failure_items, start=1):
                item_id = item.get("item_id", 0)
                item_label = f"item {item_id}" if int(item_id) > 0 else "item N/A"
                summary_lines.append(
                    f"{idx}. {item.get('scenario')} / {item_label} / {item.get('action_type')} / {item.get('result')}"
                )
                summary_lines.append(f"   - 항목명: {item.get('item_name')}")
                summary_lines.append(f"   - 요약: {item.get('summary')}")
                summary_lines.append(f"   - 스크린샷: {item.get('screenshot', 'N/A')}")
                summary_lines.append("")
        else:
            summary_lines.append("- 없음")
            summary_lines.append("")

        summary_lines.extend(
            [
                "• *조치 우선순위*:",
                "- 1순위: 비정상 항목 확인",
                "- 2순위: 판단불가 항목 스크린샷 재검토",
            ]
        )

        slack_summary_message = "\n".join(summary_lines)
        
        # 8. Slack 최종 알림 및 SMS 발송
        has_failure = failed_count > 0 or total_failure_items > 0

        if not has_failure:
            print("\n🎉 모든 테스트 통과!")
            slack_notifier.send_text(slack_summary_message)
        else:
            print(f"\n⚠️ {failed_count}개 시나리오 실패 / 비정상 항목 {total_failure_items}건")
            slack_notifier.send_text(slack_summary_message)
            sms_notifier.send_fail_alert()
        
        # 종료 전 대기
        await page.wait_for_timeout(3000)
        print("\n✨ 테스트 완료!")


if __name__ == "__main__":
    try:
        args = parse_cli_args()
        if args.item is not None:
            if args.scenario != "career_profile":
                raise ValueError("--item 옵션은 --scenario career_profile 과 함께만 사용할 수 있습니다.")
            if args.item < 1:
                raise ValueError("--item 값은 1 이상의 정수여야 합니다.")

        asyncio.run(main(selected_scenario=args.scenario, selected_item=args.item))
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류 발생: {e}")
