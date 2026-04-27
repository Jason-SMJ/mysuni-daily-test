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
    skip_reason: str | None = None  # 설정 시 자동 스킵 + 결과에 사유 표시


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


# ══════════════════════════════════════════════════════════════
# LMS_PC 점검 항목 (8항목)
# ══════════════════════════════════════════════════════════════

LMS_PC_ITEMS: list[ChecklistItem] = [
    ChecklistItem(
        service="lms_pc",
        check_item="로그인",
        check_detail="toktok SSO 또는 직접 ID/PWD 입력으로 로그인한다.",
        expected_result="로그인에 성공하고 LMS 메인페이지로 이동한다.",
        mode="hybrid",
        action_type="click",
        page_path="/",
        data_testids=["btn-login", "login-button"],
        semantic_candidates=["로그인", "Login"],
        structural_selectors=["button:has-text('로그인')", "input[type='submit']"],
        reference_image="lms_pc/01_login.png",
    ),
    ChecklistItem(
        service="lms_pc",
        check_item="카드 확인",
        check_detail="메인페이지 노출카드를 선택하여 클릭한다.",
        expected_result="선택한 카드의 상세 페이지로 정상 이동한다.",
        mode="llm",
        action_type="navigate",
        page_path="/",
        data_testids=["card-item", "learning-card"],
        semantic_candidates=[],
        structural_selectors=[
            "[class*='card'] a",
            "[class*='Card'] a",
            "a[href*='/card/']",
        ],
        reference_image="lms_pc/02_card_detail.png",
    ),
    ChecklistItem(
        service="lms_pc",
        check_item="큐브 확인",
        check_detail="조회된 카드 상세 페이지 LNB에서 Video 큐브를 클릭한다.",
        expected_result="큐브 상세 페이지로 이동되고, 우측에 판업토 플레이어가 노출된다.",
        mode="llm",
        action_type="click",
        page_path="/",
        data_testids=["cube-video", "cube-item-video"],
        semantic_candidates=["Video", "영상"],
        structural_selectors=[
            "[class*='cube']:has-text('Video')",
            "li:has-text('Video') a",
            "a[href*='/cube/']",
        ],
        reference_image="lms_pc/03_cube_detail.png",
    ),
    ChecklistItem(
        service="lms_pc",
        check_item="영상 확인",
        check_detail="노출된 판업토 플레이어에서 재생 버튼을 클릭한 후, 이어서 중단 버튼을 클릭하고 학습상태 변경을 확인한다.",
        expected_result="영상이 재생되고, 이후 영상이 중단된다.",
        mode="hybrid",
        action_type="click",
        page_path="/",
        data_testids=["player-play", "btn-play", "video-play-button"],
        semantic_candidates=["재생", "Play"],
        structural_selectors=[
            "button[aria-label*='재생']",
            "button[aria-label*='play' i]",
            "[class*='player'] button",
        ],
        reference_image="lms_pc/04_video_playing.png",
    ),
    ChecklistItem(
        service="lms_pc",
        check_item="검색 확인",
        check_detail="메인페이지로 돌아와 상단 검색창에 검색어를 입력하여 검색한다.",
        expected_result="검색결과가 노출될 수 있는 '디지털', 'AI', 'ESG' 등으로 검색 시, 검색결과가 정상 출력된다.",
        mode="llm",
        action_type="click",
        page_path="/",
        data_testids=["search-input", "search-box", "header-search"],
        semantic_candidates=["검색"],
        structural_selectors=[
            "input[type='search']",
            "input[placeholder*='검색']",
            "[class*='search'] input",
        ],
        reference_image="lms_pc/05_search_result.png",
    ),
    ChecklistItem(
        service="lms_pc",
        check_item="배지 확인",
        check_detail="Certification 메뉴로 접근 후 배지를 선택하여 도전 및 도전 취소 처리를 한다.",
        expected_result="도전 시 도전이 시작되었다는 메세지 안내후 도전이 시작된다. 도전 취소시 도전 취소 confirm 문이 노출되고, 수락시 도전이 취소된다.",
        mode="hybrid",
        action_type="popup",
        page_path="/",
        data_testids=["btn-badge-challenge", "badge-challenge-button"],
        semantic_candidates=["도전", "도전하기", "Challenge"],
        structural_selectors=[
            "button:has-text('도전')",
            "button:has-text('Challenge')",
            "[class*='badge'] button",
        ],
        popup_close_candidates=["닫기", "취소", "확인"],
        reference_image="lms_pc/06_badge_challenge.png",
    ),
    ChecklistItem(
        service="lms_pc",
        check_item="커뮤니티 확인",
        check_detail="Community 메뉴로 접근 후 가입되어 있는 커뮤니티 게시판에 게시글을 작성 후, 삭제 처리를 한다.",
        expected_result="게시글 작성 후 리스트에 정상 노출되며, 게시글을 클릭하면 상세페이지로 이동한다. 상세페이지 이동 후, 삭제 처리를 하고, 처리가 완료되면 게시글로 이동한다.",
        mode="hybrid",
        action_type="click",
        page_path="/",
        data_testids=["btn-write-post", "community-write", "post-write"],
        semantic_candidates=["글쓰기", "작성", "새 글"],
        structural_selectors=[
            "button:has-text('글쓰기')",
            "button:has-text('작성')",
            "a:has-text('글쓰기')",
        ],
        reference_image="lms_pc/07_community_post.png",
    ),
    ChecklistItem(
        service="lms_pc",
        check_item="로그아웃",
        check_detail="우측 상단의 프로필 > 로그아웃을 클릭한다.",
        expected_result="로그아웃에 성공하고, 로그인 페이지로 이동된다.",
        mode="llm",
        action_type="click",
        page_path="/",
        data_testids=["btn-logout", "logout-button"],
        semantic_candidates=["로그아웃", "Logout", "Sign out"],
        structural_selectors=[
            "a:has-text('로그아웃')",
            "button:has-text('로그아웃')",
            "[class*='logout']",
        ],
        reference_image="lms_pc/08_logout.png",
    ),
]


# ══════════════════════════════════════════════════════════════
# LMS_AI 점검 항목 (6항목)
# ══════════════════════════════════════════════════════════════

LMS_AI_ITEMS: list[ChecklistItem] = [
    ChecklistItem(
        service="lms_ai",
        check_item="학습도우미 실행",
        check_detail="mySUNI 학습도우미 아이콘 정상 실행 점검",
        expected_result="mySUNI 학습 카드/큐브 학습도우미 아이콘 정상 로딩 및 애니메이션 효과 및 실행 확인한다.",
        mode="hybrid",
        action_type="click",
        page_path="/",
        data_testids=["ai-assistant-button", "learning-helper-icon", "chatbot-button"],
        semantic_candidates=["학습도우미", "AI 도우미", "도우미"],
        structural_selectors=[
            "[class*='assistant'] button",
            "[class*='chatbot'] button",
            "button[aria-label*='도우미']",
            "button[aria-label*='assistant' i]",
        ],
        reference_image="lms_ai/01_assistant_open.png",
    ),
    ChecklistItem(
        service="lms_ai",
        check_item="ProActive 버튼 표시",
        check_detail="학습도우미 로딩 후 풍선말 형태로 '조핵심요약, 주요용어, 연관 강의' 답변 표시 여부 점검 (조핵심심요약,주요용어는 존재하는 카드,큐브에 한함)",
        expected_result="학습도우미 애니메이션 실행과 동시에 풍선말 형태로 답변 문구 표시를 확인한다.",
        mode="llm",
        action_type="none",
        page_path="/",
        reference_image="lms_ai/02_proactive_display.png",
    ),
    ChecklistItem(
        service="lms_ai",
        check_item="ProActive 과정 추천 내용",
        check_detail="ProActive 버튼을 클릭하여 발화 내용이 자동입력되고, 결과가 표시되는지 점검 (조핵심심요약,주요용어 존재 카드,큐브에 한함)",
        expected_result="클릭한 ProActive 과정 추천내용에 대한 답변 표시 확인한다.",
        mode="hybrid",
        action_type="click",
        page_path="/",
        data_testids=["proactive-btn", "proactive-button", "summary-button"],
        semantic_candidates=["핵심요약", "주요용어", "연관 강의", "ProActive"],
        structural_selectors=[
            "[class*='proactive'] button",
            "button:has-text('핵심요약')",
            "button:has-text('주요용어')",
        ],
        reference_image="lms_ai/03_proactive_result.png",
    ),
    ChecklistItem(
        service="lms_ai",
        check_item="일반발화(과정탐색)",
        check_detail="발화 창에 '파이썬 강의의 찾아줘' 입력하여 관련된 카드목록이 표시되는지 점검",
        expected_result="mySUNI에 등록된 파이썬 관련 과정 목록 표시 확인한다.",
        mode="llm",
        action_type="click",
        page_path="/",
        data_testids=["chat-input", "assistant-input", "message-input"],
        semantic_candidates=["메시지 입력", "질문을 입력"],
        structural_selectors=[
            "[class*='chat'] input",
            "[class*='assistant'] input",
            "textarea[placeholder*='입력']",
            "input[placeholder*='입력']",
        ],
        reference_image="lms_ai/04_course_search_result.png",
    ),
    ChecklistItem(
        service="lms_ai",
        check_item="일반발화(지식검색)",
        check_detail="발화 창에 '감수성이 뭐야?' 입력하여 이의 답변이 표시되는지 점검",
        expected_result="감수성과 관련된 내용 설명 표시 확인한다.",
        mode="llm",
        action_type="click",
        page_path="/",
        data_testids=["chat-input", "assistant-input", "message-input"],
        semantic_candidates=["메시지 입력", "질문을 입력"],
        structural_selectors=[
            "[class*='chat'] input",
            "[class*='assistant'] input",
            "textarea[placeholder*='입력']",
            "input[placeholder*='입력']",
        ],
        reference_image="lms_ai/05_knowledge_search_result.png",
    ),
    ChecklistItem(
        service="lms_ai",
        check_item="기타기능",
        check_detail="새대화, 이전대화, 좋아요/싫어요, 싫어요 선택시 상세 사유 선택 등의 학습도우미 기타 기능 점검",
        expected_result="개별 기능 선택시 관련된 세부 페이지가 정상적으로 표시되는지 확인한다.",
        mode="llm",
        action_type="click",
        page_path="/",
        data_testids=["btn-new-chat", "btn-history", "btn-like", "btn-dislike"],
        semantic_candidates=["새 대화", "새대화", "이전대화", "좋아요", "싫어요"],
        structural_selectors=[
            "[class*='assistant'] button[aria-label*='새']",
            "[class*='chat'] button[aria-label*='이전']",
            "button[aria-label*='좋아요']",
            "button[aria-label*='싫어요']",
        ],
        reference_image="lms_ai/06_misc_features.png",
    ),
]


# ══════════════════════════════════════════════════════════════
# LMS_Mobile 점검 항목 (10항목)
# ══════════════════════════════════════════════════════════════

LMS_MOBILE_ITEMS: list[ChecklistItem] = [
    ChecklistItem(
        service="lms_mobile",
        check_item="앱 설치",
        check_detail="앱 업데이트 안내 페이지에 접근하여 설치 안내 UI를 확인한다.",
        expected_result="다운로드 후, '설치'를 진행하면 정상 설치된다. (UI 노출 확인으로 대체)",
        mode="llm",
        action_type="navigate",
        page_path="/mobile/app/install",
        reference_image="lms_mobile/01_app_install.png",
    ),
    ChecklistItem(
        service="lms_mobile",
        check_item="로그인",
        check_detail="ID, Password를 입력하고 '로그인' 버튼을 클릭한다.",
        expected_result="올바른 데이터 입력 시, 로그인에 성공하고, 마이홀 페이지로 이동된다.",
        mode="hybrid",
        action_type="click",
        page_path="/",
        data_testids=["btn-login", "login-button"],
        semantic_candidates=["로그인", "Login"],
        structural_selectors=["button:has-text('로그인')"],
        reference_image="lms_mobile/02_login.png",
    ),
    ChecklistItem(
        service="lms_mobile",
        check_item="카드 확인",
        check_detail="마이홀페이지의 카드들에서 특정 카드를 선택하여 클릭한다.",
        expected_result="선택한 카드의 카드 상세 페이지(콘텐츠 탭)로 정상 이동된다.",
        mode="llm",
        action_type="navigate",
        page_path="/",
        data_testids=["card-item", "learning-card"],
        semantic_candidates=[],
        structural_selectors=[
            "[class*='card'] a",
            "a[href*='/card/']",
        ],
        reference_image="lms_mobile/03_card_detail.png",
    ),
    ChecklistItem(
        service="lms_mobile",
        check_item="큐브 확인",
        check_detail="조회된 카드 상세 페이지 콘텐츠 목록에서 Video 큐브를 클릭한다.",
        expected_result="큐브 상세 페이지로 이동되고, 상단에 판업토 플레이어가 노출된다.",
        mode="llm",
        action_type="click",
        page_path="/",
        data_testids=["cube-video", "cube-item-video"],
        semantic_candidates=["Video", "영상"],
        structural_selectors=[
            "[class*='cube']:has-text('Video')",
            "li:has-text('Video') a",
        ],
        reference_image="lms_mobile/04_cube_detail.png",
    ),
    ChecklistItem(
        service="lms_mobile",
        check_item="영상 확인",
        check_detail="노출된 판업토 플레이어에서 재생 버튼을 클릭한 후, 이어서 중단 버튼을 클릭하고 학습상태 변경을 확인한다.",
        expected_result="영상이 재생되고, 이후 영상이 중단된다.",
        mode="hybrid",
        action_type="click",
        page_path="/",
        data_testids=["player-play", "btn-play", "video-play-button"],
        semantic_candidates=["재생", "Play"],
        structural_selectors=[
            "button[aria-label*='재생']",
            "button[aria-label*='play' i]",
        ],
        reference_image="lms_mobile/05_video_playing.png",
    ),
    ChecklistItem(
        service="lms_mobile",
        check_item="배지 확인",
        check_detail="하단 전체 메뉴 클릭, Certification 탭으로 접근 후 배지를 선택하여 도전 및 도전 취소 처리를 한다.",
        expected_result="도전시 도전이 시작되었다는 메세지 안내후 도전이 시작된다. 도전 취소시 도전 취소 confirm 문이 노출되고, 수락시 도전이 취소된다.",
        mode="hybrid",
        action_type="popup",
        page_path="/",
        data_testids=["btn-badge-challenge", "badge-challenge-button"],
        semantic_candidates=["도전", "도전하기", "Challenge"],
        structural_selectors=[
            "button:has-text('도전')",
            "[class*='badge'] button",
        ],
        popup_close_candidates=["닫기", "취소", "확인"],
        reference_image="lms_mobile/06_badge_challenge.png",
    ),
    ChecklistItem(
        service="lms_mobile",
        check_item="커뮤니티 확인",
        check_detail="하단 커뮤니티 메뉴 클릭, 가입되어 있는 커뮤니티 게시판에 게시글을 작성 후, 삭제 처리 한다.",
        expected_result="게시글 작성 후 리스트에 정상 노출되며, 게시글을 클릭하면 상세페이지로 이동한다. 상세페이지 이동 후, 삭제 처리를 하고, 처리가 완료되면 게시글로 이동한다.",
        mode="hybrid",
        action_type="click",
        page_path="/",
        data_testids=["btn-write-post", "community-write"],
        semantic_candidates=["글쓰기", "작성"],
        structural_selectors=["button:has-text('글쓰기')", "button:has-text('작성')"],
        reference_image="lms_mobile/07_community_post.png",
    ),
    ChecklistItem(
        service="lms_mobile",
        check_item="간편로그인 설정",
        check_detail="하단 더보기 설정을 클릭한 후, 간편로그인 설정을 클릭한다. 패턴을 선택하고, 입력을 진행한다.",
        expected_result="간편로그인 3가지 방식 설정을 위한 대화상자가 출력된다. 패턴 입력창이 뜨고, 2번 동일한 패턴 입력 시, 창이 정상 종료된다.",
        mode="hybrid",
        action_type="click",
        page_path="/",
        data_testids=["btn-easy-login-setting", "easy-login-setting"],
        semantic_candidates=["간편로그인 설정", "간편 로그인 설정", "패턴"],
        structural_selectors=[
            "button:has-text('간편로그인')",
            "a:has-text('간편로그인')",
        ],
        reference_image="lms_mobile/08_easy_login_setup.png",
    ),
    ChecklistItem(
        service="lms_mobile",
        check_item="로그아웃",
        check_detail="하단 더보기의 로그아웃을 클릭한다.",
        expected_result="로그아웃에 성공하고, 로그인 페이지로 이동된다.",
        mode="llm",
        action_type="click",
        page_path="/",
        data_testids=["btn-logout", "logout-button"],
        semantic_candidates=["로그아웃", "Logout"],
        structural_selectors=["a:has-text('로그아웃')", "button:has-text('로그아웃')"],
        reference_image="lms_mobile/09_logout.png",
    ),
    ChecklistItem(
        service="lms_mobile",
        check_item="간편로그인",
        check_detail="로그인 창의 '간편 로그인' 버튼을 클릭한다.",
        expected_result="위에서 설정한 패턴 입력창이 뜨고 올바른 패턴 입력 시, 마이홀 페이지로 이동된다.",
        mode="hybrid",
        action_type="click",
        page_path="/",
        data_testids=["btn-easy-login", "easy-login-button"],
        semantic_candidates=["간편 로그인", "간편로그인"],
        structural_selectors=["button:has-text('간편 로그인')", "button:has-text('간편로그인')"],
        reference_image="lms_mobile/10_easy_login.png",
    ),
]


# ══════════════════════════════════════════════════════════════
# Career 확장 점검 항목 (7항목: Career추천 + My Pick)
# ══════════════════════════════════════════════════════════════

CAREER_EXTENDED_ITEMS: list[ChecklistItem] = [
    ChecklistItem(
        service="career_extended",
        check_item="Career 추천 이동",
        check_detail="Career추천 메뉴에서 현재직무, 완료한 학습, Project를 기반으로 3가지 직무를 추천하고 Pick 버튼 클릭 시 희망직무로 설정한다.",
        expected_result="추천된 직무에 따른 세부정보(매칭율, 이슈과정, 취득 Skill 정보)를 제공하고 Pick 버튼 클릭 시 희망직무로 설정하고 다시 보기 시 하단의 플로팅 메뉴에서 직업 편집이 가능하다.",
        mode="llm",
        action_type="navigate",
        page_path="/career/recommend",
        data_testids=["menu-career-recommend", "career-recommend"],
        semantic_candidates=["Career 추천", "직무 추천"],
        structural_selectors=[
            "a[href*='recommend']",
            "[class*='recommend']",
        ],
        reference_image="career_extended/01_career_recommend.png",
    ),
    ChecklistItem(
        service="career_extended",
        check_item="Career 추천 직무 미리보기",
        check_detail="희망직무 Pick하기 전 추천된 직무를 클릭한다.",
        expected_result="희망직무로 Pick하기 전에 추천된 직무를 클릭한 경우 My Pick 미리보기(읽기전용)화면으로 이동한다.",
        mode="hybrid",
        action_type="click",
        page_path="/career/recommend",
        data_testids=["recommend-job-item", "job-preview-btn"],
        semantic_candidates=["미리보기", "직무 상세"],
        structural_selectors=[
            "[class*='recommend'] [class*='job']",
            "[class*='recommend'] li",
        ],
        reference_image="career_extended/02_job_preview.png",
    ),
    ChecklistItem(
        service="career_extended",
        check_item="Career 탐색",
        check_detail="Career추천 화면에서 사내직무를 선택하거나 직무를 검색한다.",
        expected_result="Career탐색에서 기본으로 사내직무를 10개씩 제공하고 더보기 할 수 있다. 직무를 검색하여 조회된 직무를 선택하여 희망직무로 설정 할 수 있다.",
        mode="llm",
        action_type="click",
        page_path="/career/recommend",
        data_testids=["career-explore", "job-search-input", "career-search"],
        semantic_candidates=["직무 검색", "탐색", "더보기"],
        structural_selectors=[
            "input[placeholder*='직무']",
            "button:has-text('더보기')",
            "[class*='explore']",
        ],
        reference_image="career_extended/03_career_explore.png",
    ),
    ChecklistItem(
        service="career_extended",
        check_item="My Pick",
        check_detail="메뉴 접근 시 현재직무, 희망직무 별 대시보드 정보 및 스킬 목록, 러닝패스가 노출된다.",
        expected_result="기본으로 현재 직무 정보를 확인하고 Skill Match Progress, Learning Path Progress 그래프, 스킬정보, 러닝패스를 추천한다.",
        mode="llm",
        action_type="navigate",
        page_path="/career/my-pick",
        data_testids=["menu-my-pick", "my-pick"],
        semantic_candidates=["My Pick", "마이픽"],
        structural_selectors=[
            "a[href*='my-pick']",
            "[class*='my-pick']",
        ],
        reference_image="career_extended/04_my_pick.png",
    ),
    ChecklistItem(
        service="career_extended",
        check_item="My Pick에서 직무Tab",
        check_detail="상단 직무명 Tap, Career추천받기 Tab을 클릭한다.",
        expected_result="직무명 Tab 클릭 시 해당 직무의 정보로 전환된다. 추천받기 Tab 클릭 시 Career추천 메뉴로 이동한다.",
        mode="hybrid",
        action_type="click",
        page_path="/career/my-pick",
        data_testids=["job-tab", "recommend-tab", "my-pick-tab"],
        semantic_candidates=["현재직무", "희망직무", "추천받기"],
        structural_selectors=[
            "[class*='tab'] button",
            "button[role='tab']",
        ],
        reference_image="career_extended/05_mypick_job_tab.png",
    ),
    ChecklistItem(
        service="career_extended",
        check_item="My Pick에서 직무별 Skill 정보 확인",
        check_detail="Skill 목록 펼쳐보기 버튼을 클릭 한다.",
        expected_result="선택한 직무의 Task와 Skill이 펼쳐진다. 구성원 본인이 보유하고 있는 스킬과 레벨이 표시되며 스킬을 선택하면 적절 레벨을 수정하거나 미보유 상태로 변경 할 수 있다.",
        mode="hybrid",
        action_type="click",
        page_path="/career/my-pick",
        data_testids=["skill-expand-btn", "skill-list-expand", "task-expand"],
        semantic_candidates=["펼쳐보기", "더보기", "스킬 목록"],
        structural_selectors=[
            "button:has-text('펼쳐보기')",
            "button[aria-expanded='false']",
            "[class*='skill'] button",
        ],
        reference_image="career_extended/06_skill_expand.png",
    ),
    ChecklistItem(
        service="career_extended",
        check_item="My Pick에서 Learning Path추천",
        check_detail="현재 보유중인 스킬을 기반으로 선택한 직무에 필요한 Learning Path를 추천한다.",
        expected_result="추천된 학습과정, Badge, Certificate는 사용자가 추가/삭제 처리가 가능하며 각 카드를 클릭하여 상세 정보를 확인한다. 'Learning Path 추천 다시받기'를 클릭하면 초기화하고 새로운 러닝패스를 추천한다.",
        mode="llm",
        action_type="none",
        page_path="/career/my-pick",
        reference_image="career_extended/07_learning_path.png",
    ),
]


# ══════════════════════════════════════════════════════════════
# One_ID 점검 항목 (5항목: 일반사용자만)
# ══════════════════════════════════════════════════════════════

ONE_ID_ITEMS: list[ChecklistItem] = [
    ChecklistItem(
        service="one_id",
        check_item="로그인 페이지",
        check_detail="https://mysuni.sk.com 통해 통합ID 로그인 사이트 접속한다.",
        expected_result="로그인 페이지가 열리며, ID/PWD 입력창이 활성화 된다.",
        mode="llm",
        action_type="navigate",
        page_path="/",
        reference_image="one_id/01_login_page.png",
    ),
    ChecklistItem(
        service="one_id",
        check_item="로그인",
        check_detail="ID, Password를 입력하고 '로그인' 버튼을 클릭한다.",
        expected_result="올바른 데이터 입력 시, 로그인에 성공하고, LMS로 이동한다.",
        mode="hybrid",
        action_type="click",
        page_path="/",
        data_testids=["btn-login", "login-button"],
        semantic_candidates=["로그인", "Login"],
        structural_selectors=["button:has-text('로그인')", "input[type='submit']"],
        reference_image="one_id/02_login.png",
    ),
    ChecklistItem(
        service="one_id",
        check_item="ID 찾기",
        check_detail="로그인 내 'ID 또는 비밀번호를 잊으셨나요?' 클릭 후 'ID찾기' 탭에서 이름, 핸드폰 번호 입력 후 인증번호 발송 및 인증 한다.",
        expected_result="이름/핸드폰번호로, 사용자의 ID 목록이 노출된다.",
        mode="hybrid",
        action_type="click",
        page_path="/",
        data_testids=["find-id-tab", "btn-find-id"],
        semantic_candidates=["ID 찾기", "아이디 찾기", "ID 또는 비밀번호"],
        structural_selectors=[
            "a:has-text('ID 찾기')",
            "button:has-text('ID 찾기')",
            "a:has-text('비밀번호를 잊으셨나요')",
        ],
        reference_image="one_id/03_find_id.png",
    ),
    ChecklistItem(
        service="one_id",
        check_item="개인정보처리방침",
        check_detail="하단 개인정보처리방침을 클릭한다.",
        expected_result="개인정보처리방침 페이지가 정상적으로 열린다. SK그룹사, 일반사용자 탭이 노출된다.",
        mode="llm",
        action_type="click",
        page_path="/",
        data_testids=["privacy-policy", "btn-privacy"],
        semantic_candidates=["개인정보처리방침", "개인정보 처리방침"],
        structural_selectors=[
            "a:has-text('개인정보처리방침')",
            "footer a:has-text('개인정보')",
        ],
        reference_image="one_id/04_privacy_policy.png",
    ),
    ChecklistItem(
        service="one_id",
        check_item="내정보",
        check_detail="LMS > myPage > 프로필 설정 페이지 내 '정보설정' 버튼을 클릭하여 통합ID 내정보 사이트로 이동한다.",
        expected_result="내정보 페이지에서 회원정보, 구성원정보, 직무정보가 노출된다.",
        mode="llm",
        action_type="navigate",
        page_path="/suni-main/mypage?page=/profile-setting",
        data_testids=["btn-info-setting", "info-setting"],
        semantic_candidates=["정보설정", "내정보", "회원정보"],
        structural_selectors=[
            "button:has-text('정보설정')",
            "a:has-text('정보설정')",
        ],
        reference_image="one_id/05_my_info.png",
    ),
]
