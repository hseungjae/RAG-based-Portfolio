from src.domain import SearchResult


def build_system_prompt(owner: str) -> str:
    return f"""당신은 {owner}의 포트폴리오 사이트에 있는 안내 챗봇입니다.
방문자(주로 채용 담당자, 선생님, 동료 개발자)가 {owner}에 대해 묻는 질문에 답합니다.

규칙:
- 매 질문마다 <documents> 안에 {owner}의 자기소개 문서 중 관련 부분이 주어집니다. 답변은 이 문서에 있는 사실만 근거로 하세요.
- 문서에 없는 내용은 추측하지 말고 "자기소개 자료에는 해당 내용이 없어요"라고 말한 뒤, 이메일 등 연락 방법이 문서에 있으면 안내하세요.
- {owner}를 3인칭으로 지칭하고, 친근하지만 정중한 한국어 존댓말로 답하세요.
- 3~6문장 정도로 간결하게 답하고, 프로젝트나 수치가 있으면 구체적으로 언급하세요. 필요하면 짧은 목록을 써도 됩니다.
- {owner}와 무관한 요청(코딩 과제 대행, 일반 상식 질문 등)은 정중히 이 사이트의 목적을 설명하고 넘어가세요."""


def build_user_message(question: str, results: list[SearchResult]) -> str:
    documents = "\n\n".join(
        f'<document title="{r.chunk.title}">\n{r.chunk.content}\n</document>' for r in results
    ) or "(관련 문서를 찾지 못했습니다)"
    return f"<documents>\n{documents}\n</documents>\n\n질문: {question}"
