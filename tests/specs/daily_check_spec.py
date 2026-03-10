"""일일점검 Spec 정의: 서비스별 Test Item."""

from dataclasses import dataclass, field
from typing import Literal

ValidationMode = Literal["playwright", "llm", "hybrid"]
ActionType = Literal["none", "navigate", "click", "popup"]


@dataclass(frozen=True)
class ChecklistItem:
    service: str
    check_item: str
    check_detail: str
    expected_result: str
    mode: ValidationMode = "hybrid"
    action_type: ActionType = "none"
    page_path: str = "/suni-main/career?page=/main"
    data_testids: list[str] = field(default_factory=list)
    semantic_candidates: list[str] = field(default_factory=list)
    structural_selectors: list[str] = field(default_factory=list)
    popup_close_candidates: list[str] = field(default_factory=list)
    reference_image: str | None = None


CAREER_PROFILE_ITEMS: list[ChecklistItem] = [
    ChecklistItem(
        service="career_profile",
        check_item="Career 메뉴 이동",
        check_detail="Career 권한이 있는 계정으로 로그인 후 Career 메뉴를 클릭한다.",
        expected_result="Career Profile 화면으로 이동한다.",
        mode="hybrid",
        action_type="navigate",
        data_testids=["menu-career", "nav-career"],
        semantic_candidates=["Career", "커리어"],
        structural_selectors=["a[href*='career']", "button:has-text('Career')"],
        reference_image="career_profile/01_career_menu.png",
    ),
    ChecklistItem(
        service="career_profile",
        check_item="Skill SUMMARY 확인",
        check_detail="현재 직무, Internal Status, Global Market Trend 정보를 확인한다.",
        expected_result=(
            "요약 영역에 현재 직무/트렌드/상태 등의 요약 정보가 보인다. "
            "일부 데이터가 없더라도 로딩 오류/빈 화면이 아닌 정상 UI 상태(섹션/카드/라벨)가 확인된다."
        ),
        mode="llm",
        reference_image="career_profile/02_skill_summary.png",
    ),
    ChecklistItem(
        service="career_profile",
        check_item="My Skill 정보",
        check_detail="현재 직무 보유 Task & Skill, others Skill, Core Skill 정보를 확인한다.",
        expected_result=(
            "My Skill 섹션에서 Task & Skill / Others Skill / Core Skill 영역이 구분되어 보인다. "
            "데이터가 없다면 안내/빈 상태 UI가 보이고, 깨짐/로딩만/오류 화면이면 비정상이다."
        ),
        mode="llm",
        reference_image="career_profile/03_my_skill.png",
    ),
    ChecklistItem(
        service="career_profile",
        check_item="Project 정보 확인",
        check_detail="Project 정보를 확인한다.",
        expected_result=(
            "Project 섹션이 정상 노출된다. 프로젝트가 존재하면 기간/이름/역할/설명/스킬 등 상세가 확인되고, "
            "없으면 등록 유도/빈 상태 UI가 보인다."
        ),
        mode="llm",
        reference_image="career_profile/04_project_info.png",
    ),
    ChecklistItem(
        service="career_profile",
        check_item="Badge & Certificate 정보 확인",
        check_detail="Badge & Certification 정보를 확인한다.",
        expected_result=(
            "정책/안내 문구(연동 안내 포함) 또는 관련 정보가 노출된다. "
            "데이터가 없는 경우에도 아래 문구가 보이면 정상이다: "
            "'Badge & Certification 정보는 각각 mySUNI 및 회사별 E-HR에서 연동되므로, 각 시스템의 정보를 확인해 주세요.'"
        ),
        mode="llm",
        reference_image="career_profile/05_badge_certificate.png",
    ),
    ChecklistItem(
        service="career_profile",
        check_item="학습과정 정보 확인",
        check_detail="mySUNI 학습과정 정보를 확인한다.",
        expected_result=(
            "학습과정 섹션이 정상 노출된다. 데이터가 있으면 기간/과정명/기관/시간/스킬 등의 정보가 보이고, "
            "없으면 빈 상태/안내 문구가 보인다."
        ),
        mode="llm",
        reference_image="career_profile/06_learning_info.png",
    ),
    ChecklistItem(
        service="career_profile",
        check_item="학력 및 경력 정보 확인",
        check_detail="학력/경력 정보 영역 노출 여부를 확인한다.",
        expected_result=(
            "HR 관련 정보가 있으면 노출된다. 없으면 아래 문구가 보이면 정상이다: "
            "'학력 정보는 회사별 E-HR에서 연동됩니다. E-HR 정보를 확인해 주세요.' / "
            "'경력 정보는 회사별 E-HR에서 연동됩니다. E-HR 정보를 확인해 주세요.'"
        ),
        mode="llm",
        reference_image="career_profile/07_education_career.png",
    ),
    ChecklistItem(
        service="career_profile",
        check_item="Skill 수정하기",
        check_detail="'Skill 수정하기' 버튼 클릭 후 스킬 추가/수정 가능 여부를 확인한다.",
        expected_result=(
            "My Skill 편집 모드로 전환되어 수정 가능한 상태가 보인다(예: 완료 버튼, 편집 UI, Task/Skill 선택 UI). "
            "편집 모드가 팝업/인페이지 어느 형태든 정상으로 인정한다."
        ),
        mode="hybrid",
        action_type="click",
        data_testids=["profile-user-skill-edit-button", "btn-skill-edit", "skill-edit"],
        semantic_candidates=["Skill 수정하기", "수정하기", "스킬 수정", "완료"],
        structural_selectors=["button:has-text('수정')", "button:has-text('완료')"],
        reference_image="career_profile/08_skill_edit.png",
    ),
    ChecklistItem(
        service="career_profile",
        check_item="Project 정보 등록/수정",
        check_detail="Project의 수정 또는 + 버튼 동작을 확인한다.",
        expected_result=(
            "Project 등록/수정 UI(팝업/드로어/레이어 등)로 진입한다. "
            "제목/필드/버튼 등 입력 가능한 폼 UI가 확인된다."
        ),
        mode="hybrid",
        action_type="popup",
        data_testids=["profile-user-project-add-button", "project-add", "project-edit"],
        semantic_candidates=["Project 등록", "Project 수정", "프로젝트 등록", "프로젝트 수정"],
        structural_selectors=[
            "section:has-text('Project') button:has-text('등록')",
            "section:has-text('Project') button:has-text('수정')",
            "section:has-text('Project') button[aria-label*='add' i]",
        ],
        popup_close_candidates=["닫기", "취소", "X", "Close"],
        reference_image="career_profile/09_project_popup.png",
    ),
    ChecklistItem(
        service="career_profile",
        check_item="학습과정 정보 등록/수정",
        check_detail="mySUNI 학습과정과 외부학습 등록/수정 가능 여부를 확인한다.",
        expected_result=(
            "학습과정(+)/외부학습 등록/수정 UI로 진입한다. "
            "학습 과정 검색(팝업 타이틀), 학습기관선택/학습 과정, 검색 버튼 등 입력 가능한 폼 UI가 확인된다."
        ),
        mode="hybrid",
        action_type="popup",
        data_testids=["profile-user-learning-add-button", "learning-add", "learning-edit", "external-learning-add"],
        semantic_candidates=["학습과정 등록", "외부학습 등록", "학습과정 수정", "외부학습 수정"],
        structural_selectors=[
            "section:has-text('학습과정') button:has-text('등록')",
            "section:has-text('학습과정') button:has-text('수정')",
            "section:has-text('외부학습') button:has-text('등록')",
            "section:has-text('학습과정') button[aria-label*='add' i]",
        ],
        popup_close_candidates=["닫기", "취소", "X", "Close"],
        reference_image="career_profile/10_learning_popup.png",
    ),
]
