"""
Azure OpenAI Vision API 통합 모듈
스크린샷을 분석하여 화면의 정상/비정상 여부를 판별합니다.
"""

import re
from typing import Dict, Tuple, Literal, Optional
from openai import AzureOpenAI


class AzureVisionClient:
    """Azure OpenAI Vision API를 사용한 화면 검증 클라이언트"""
    
    # 프롬프트 템플릿
    PROMPTS = {
        "lenient": (
            "#아래 스크린샷이 정상 화면인지 판별해줘.\n"
            "##- 정상 화면: 주요 콘텐츠(추천 강의 카드, 텍스트, 버튼 등)가 표시되면 정상으로 본다.\n"
            "##- 비정상 화면: 화면이 비어있거나, 오류 메시지, 로딩 아이콘만 있는 경우.\n"
            "#애매하면 정상으로 판정해."
        ),
        "strict": (
            "#아래 스크린샷이 정상 화면인지 판별해줘.\n"
            "##정상으로 간주하려면 다음 두 조건을 모두 충족해야 한다: "
            "###(A) 페이지의 핵심 UI(제목/본문/버튼/카드 등) 중 2개 이상이 명확히 보일 것, "
            "###(B) 주요 텍스트가 읽을 수 있는 크기와 해상도로 표시될 것.\n"
            "##다음 중 하나라도 보이면 비정상으로 판정한다: "
            "###로딩 아이콘/스켈레톤/빈 화면/에러 메시지/깨진 UI/요소 겹침/"
            "###너무 작아 읽기 어려운 축소 뷰/콘텐츠 미표시.\n"
            "##애매하면 비정상으로 판정해."
        )
    }
    
    SYSTEM_PROMPT = (
        "너는 QA 테스트 어시스턴트야. "
        "스크린샷을 보고 정상/비정상 여부를 판별해."
        "결과는 '정상', '비정상', '판단불가' 중 하나로만 대답해."
        "첫 줄은 반드시 '판정: 정상|비정상|판단불가' 형식으로 작성해."
        "단계별로 분석하세요:"
        "Step 1: 레이아웃 구조"
        "Step 2: UI 요소 확인"
        "Step 3: 콘텐츠 품질"
        "Step 4: 에러 여부"
        "Step 5: 최종 판정"
    )
    
    def __init__(self, config: Dict[str, str]):
        """
        Args:
            config: Azure OpenAI 설정
                - endpoint: Azure OpenAI 엔드포인트
                - api_key: API 키
                - api_version: API 버전
                - deployment: 배포 모델명
        """
        self.client = AzureOpenAI(
            azure_endpoint=config["endpoint"],
            api_key=config["api_key"],
            api_version=config["api_version"],
        )
        self.deployment = config["deployment"]
    
    def validate_screenshot(
        self,
        image_data_url: str,
        validation_mode: Literal["lenient", "strict"] = "strict",
        custom_prompt: Optional[str] = None,
        reference_image_data_url: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        스크린샷을 분석하여 정상/비정상 여부를 판별합니다.
        Args:
            image_data_url: data:image/png;base64,... 형식의 이미지 URL
            validation_mode: 검증 모드 ("lenient" 또는 "strict")
            custom_prompt: 커스텀 검증 프롬프트 (지정 시 validation_mode 대신 사용)
            reference_image_data_url: 비교용 기준 이미지 URL (선택)
        Returns:
            (판정결과, LLM 응답 전문) 튜플
            판정결과: "정상", "비정상", "판단불가" 중 하나
        """
        prompt = custom_prompt or self.PROMPTS[validation_mode]
        print(f"🤖 Prompt 응답: {prompt}")

        user_content = [{"type": "text", "text": prompt}]
        if reference_image_data_url:
            user_content.append({"type": "text", "text": "기준 이미지"})
            user_content.append({"type": "image_url", "image_url": {"url": reference_image_data_url}})
            user_content.append({"type": "text", "text": "실행 결과 이미지"})
        user_content.append({"type": "image_url", "image_url": {"url": image_data_url}})
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": self.SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": user_content
                    }
                ]
            )
            
            content = response.choices[0].message.content
            print(f"🤖 LLM 응답: {content}")
            
            # 응답 파싱
            result = self._parse_response(content)
            return result, content
            
        except Exception as e:
            print(f"❌ LLM 응답 처리 중 오류: {e}")
            return "판단불가", str(e)
    
    def _parse_response(self, content: str) -> str:
        """
        LLM 응답을 파싱하여 판정 결과를 추출합니다.
        Args: content: LLM 응답 텍스트
        Returns: "정상", "비정상", "판단불가" 중 하나
        """
        normalized = content.strip()

        # 1) 명시 포맷 우선 파싱 (권장 출력 형식)
        explicit_match = re.search(
            r"(?:^|\n)\s*(?:\[)?\s*(?:판정|최종\s*판정|판정\s*결과|결과)\s*[:：]\s*(정상|비정상|판단불가)",
            normalized,
        )
        if explicit_match:
            token = explicit_match.group(1)
        else:
            # 2) 선두 토큰 파싱 (마크다운 강조 포함)
            leading_token_match = re.match(
                r"^\s*(?:\*{1,2})?\s*(정상|비정상|판단불가)\s*(?:\*{1,2})?(?:\b|$)",
                normalized,
            )
            if leading_token_match:
                token = leading_token_match.group(1)
            else:
                # 3) 문장 기반 백업 규칙
                explicit_verdict_match = re.search(
                    r"(?<![가-힣A-Za-z])(정상|비정상|판단불가)(?![가-힣A-Za-z])\s*(?:['\"”`])?\s*(?:입니다|임|으로\s*판정|으로\s*판단)",
                    normalized,
                )
                if explicit_verdict_match:
                    token = explicit_verdict_match.group(1)
                else:
                    # '비정상 요소는 보이지 않음/없음' 같은 부정문은 비정상 신호에서 제외한다.
                    has_abnormal_word = "비정상" in normalized
                    has_normal_word = "정상" in normalized
                    abnormal_negated = bool(
                        re.search(r"비정상(?:적인)?\s*(?:요소|화면|징후)?\s*(?:은|가)?\s*보이지\s*않", normalized)
                        or re.search(r"비정상(?:적인)?\s*(?:요소|화면|징후)?\s*(?:은|가)?\s*없", normalized)
                    )

                    if has_abnormal_word and not abnormal_negated and not has_normal_word:
                        token = "비정상"
                    elif has_normal_word and (not has_abnormal_word or abnormal_negated):
                        token = "정상"
                    elif "판단불가" in normalized:
                        token = "판단불가"
                    else:
                        token = "판단불가"

        if token == "정상":
            print("✅ 화면 정상으로 판단")
            return "정상"
        if token == "비정상":
            print("❌ 화면 비정상으로 판단")
            return "비정상"

        print("⚠️ 판단 불가 (LLM 응답 해석 실패)")
        return "판단불가"
