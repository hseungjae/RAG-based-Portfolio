"""마크다운 문서를 '##' 섹션 단위 청크로 자른다."""

from pathlib import Path

from src.domain import Chunk


def split_markdown(path: Path, start_id: int) -> list[Chunk]:
    doc_title = path.stem
    chunks: list[Chunk] = []
    section, buf = "", []

    def flush() -> None:
        body = "\n".join(buf).strip()
        if body:
            title = f"{doc_title} > {section}" if section else doc_title
            chunks.append(Chunk(start_id + len(chunks), path.name, title, body))

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            doc_title = line[2:].strip()
        elif line.startswith("## "):
            flush()
            section, buf = line[3:].strip(), []
        else:
            buf.append(line)
    flush()
    return chunks


def load_chunks(profile_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(profile_dir.glob("*.md")):
        chunks.extend(split_markdown(path, len(chunks)))
    return chunks
