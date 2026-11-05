from src.chunk.chunker import load_chunks, split_markdown
from src.settings import settings


def test_splits_by_section(tmp_path):
    path = tmp_path / "01_about.md"
    path.write_text(
        "# 소개\n"
        "첫 섹션 전에 있는 글\n"
        "## 경력\n"
        "클라우드 엔지니어\n"
        "## 빈 섹션\n"
        "\n"
        "## 취미\n"
        "등산\n",
        encoding="utf-8",
    )

    chunks = split_markdown(path, start_id=10)

    assert [(c.chunk_id, c.source, c.title, c.content) for c in chunks] == [
        (10, "01_about.md", "소개", "첫 섹션 전에 있는 글"),
        (11, "01_about.md", "소개 > 경력", "클라우드 엔지니어"),
        # 내용이 없는 섹션은 건너뛴다
        (12, "01_about.md", "소개 > 취미", "등산"),
    ]


def test_uses_file_name_when_no_title(tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("## 메모\n내용\n", encoding="utf-8")

    assert split_markdown(path, start_id=0)[0].title == "notes > 메모"


def test_profile_dataset_loads():
    # 실제 자기소개 문서가 깨지지 않고 청크로 나뉘는지 확인한다
    chunks = load_chunks(settings.profile_dir)

    assert chunks
    assert [c.chunk_id for c in chunks] == list(range(len(chunks)))
    assert all(c.content.strip() for c in chunks)
    assert {c.source for c in chunks} == {p.name for p in settings.profile_dir.glob("*.md")}
