"""
MySuni 자동 점검 메인 실행 파일
Pilot 1단계: Career Profile 체크리스트 검증 우선 실행
"""

import asyncio
import argparse
from dataclasses import dataclass
from typing import Callable
from config.settings import Settings
from core.browser import BrowserManager, MySuniPage
from core.screenshot import ScreenshotManager
from integrations.azure_openai import AzureVisionClient
from integrations.slack_notifier import SlackNotifier

# 새로운 Career 페이지 테스트 시나리오
from tests.career_profile_test import CareerProfileTestScenario
from tests.career_recommend_test import CareerRecommendTestScenario
from tests.career_mypick_test import CareerMyPickTestScenario  
from tests.career_1on1_test import Career1on1TestScenario
from tests.career_myprogress_test import CareerMyProgressTestScenario
# from tests.career_teammgmt_test import CareerTeamManagementTestScenario
# from tests.career_teammgmt_test import CareerMTIInternalViewTestScenario
# from tests.career_teammgmt_test import CareerMTIGlobalTrendTestScenario


@dataclass
class ScenarioPlan:
    key: str
    name: str
    enabled: bool
    skip_reason: str
    factory: Callable[[], object]

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
    mysuni_config = settings.get_mysuni_credentials()
    browser_config = settings.get_browser_config()
    proxy_url = settings.get_proxy_url()
    scenario_config = {
        item.get("name", ""): item for item in settings.get_test_scenarios()
    }
    
    # 2. 클라이언트 초기화
    print("🔧 클라이언트 초기화 중...")
    vision_client = AzureVisionClient(azure_config)
    slack_notifier = SlackNotifier(slack_config, proxy_url)
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
        
        # 4. MySuni 로그인
        print("\n🔑 MySuni 로그인 중...")
        if not await mysuni_page.login(
            mysuni_config["id"], 
            mysuni_config["password"]
        ):
            print("❌ 로그인 실패")
            slack_notifier.send_text("❌ MySuni 로그인 실패")
            return
        
        print("✅ 로그인 성공")
        
        # 5. 테스트 시나리오 계획 수립
        scenario_plans = [
            ScenarioPlan(
                key="career_profile",
                name="Pilot: Career Profile",
                enabled=scenario_config.get("career_profile", {}).get("enabled", True),
                skip_reason=scenario_config.get("career_profile", {}).get("skip_reason", ""),
                factory=lambda: CareerProfileTestScenario(
                    page,
                    mysuni_page,
                    screenshot_manager,
                    vision_client,
                    slack_notifier,
                    target_item_index=selected_item,
                ),
            ),
            ScenarioPlan(
                key="career_recommend",
                name="Career Recommend",
                enabled=scenario_config.get("career_recommend", {}).get("enabled", False),
                skip_reason=scenario_config.get("career_recommend", {}).get("skip_reason", "Pilot 1단계 범위 제외"),
                factory=lambda: CareerRecommendTestScenario(
                    page, mysuni_page, screenshot_manager, vision_client, slack_notifier
                ),
            ),
            ScenarioPlan(
                key="career_mypick",
                name="Career My Pick",
                enabled=scenario_config.get("career_mypick", {}).get("enabled", False),
                skip_reason=scenario_config.get("career_mypick", {}).get("skip_reason", "Pilot 1단계 범위 제외"),
                factory=lambda: CareerMyPickTestScenario(
                    page, mysuni_page, screenshot_manager, vision_client, slack_notifier
                ),
            ),
            ScenarioPlan(
                key="career_1on1",
                name="Career Coach 1on1",
                enabled=scenario_config.get("career_1on1", {}).get("enabled", False),
                skip_reason=scenario_config.get("career_1on1", {}).get("skip_reason", "Pilot 1단계 범위 제외"),
                factory=lambda: Career1on1TestScenario(
                    page, mysuni_page, screenshot_manager, vision_client, slack_notifier
                ),
            ),
            ScenarioPlan(
                key="career_myprogress",
                name="Career Coach My Progress",
                enabled=scenario_config.get("career_myprogress", {}).get("enabled", False),
                skip_reason=scenario_config.get("career_myprogress", {}).get("skip_reason", "Pilot 1단계 범위 제외"),
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
        for i, plan in enumerate(scenario_plans, 1):
            print(f"\n[{i}/{len(scenario_plans)}] {plan.name}")
            print("-" * 60)

            should_run = True if selected_scenario else plan.enabled
            if not should_run:
                print(f"⏭️ 스킵 - 사유: {plan.skip_reason}")
                results.append((plan.name, "SKIP", plan.skip_reason))
            else:
                scenario = plan.factory()
                passed = await scenario.run()
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
            f"실패: {failed_count}, 스킵: {skipped_count}"
        )
        print("="*60)
        
        # 8. Slack 최종 알림
        if failed_count == 0:
            print("\n🎉 모든 테스트 통과!")
            slack_notifier.send_text(
                f"🎉 MySuni 일일점검 자동 검증 완료\n"
                f"✅ 성공: {passed_count}개\n"
                f"⏭️ 스킵: {skipped_count}개"
            )
        else:
            print(f"\n⚠️ {failed_count}개 테스트 실패")
            slack_notifier.send_text(
                f"⚠️ MySuni 일일점검 자동 검증 완료\n"
                f"✅ 성공: {passed_count}개\n"
                f"❌ 실패: {failed_count}개\n"
                f"⏭️ 스킵: {skipped_count}개"
            )
        
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
