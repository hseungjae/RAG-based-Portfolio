import pytest

from src.chat.prompt import (EMPTY_ANSWER, FALLBACK_ANSWER, build_system_prompt, build_user_message,
                             is_unanswered)
from src.domain import Chunk, SearchResult


@pytest.mark.parametrize("answer", [
    FALLBACK_ANSWER,
    f'"{FALLBACK_ANSWER}"',      # 프롬프트의 따옴표까지 따라 쓰는 경우
    f"  {FALLBACK_ANSWER}\n",
    EMPTY_ANSWER,
])
def test_detects_unanswered(answer):
    assert is_unanswered(answer)


@pytest.mark.parametrize("answer", [
    "저는 클라우드 엔지니어로 일했습니다.",
    f"지방대회 2등을 했습니다. {FALLBACK_ANSWER}",   # 일부라도 답했으면 답변한 것으로 본다
    "",
])
def test_normal_answer_is_not_unanswered(answer):
    assert not is_unanswered(answer)


def test_system_prompt_has_owner_and_fallback():
    prompt = build_system_prompt("홍길동")

    assert "홍길동" in prompt
    assert FALLBACK_ANSWER in prompt


def test_user_message_wraps_documents():
    results = [SearchResult(Chunk(0, "01_about.md", "소개 > 경력", "클라우드 엔지니어"), 0.8)]

    message = build_user_message("경력은?", results)

    assert '<document title="소개 > 경력">\n클라우드 엔지니어\n</document>' in message
    assert message.endswith("질문: 경력은?")


def test_user_message_without_documents():
    assert "(관련 문서를 찾지 못했습니다)" in build_user_message("안녕?", [])
