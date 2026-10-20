const log = document.getElementById("log");
const form = document.getElementById("form");
const input = document.getElementById("q");
const sendBtn = document.getElementById("send");
const history = []; // 최근 대화만 서버에 보내서 후속 질문 맥락으로 사용

fetch("/api/config").then(r => r.json()).then(c => {
  document.getElementById("owner").textContent = c.owner;
  document.title = `${c.owner} · Ask Me Anything`;
}).catch(() => {});

document.querySelectorAll(".chips button").forEach(b =>
  b.addEventListener("click", () => ask(b.textContent)));

form.addEventListener("submit", e => {
  e.preventDefault();
  const q = input.value.trim();
  if (q) ask(q);
});

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// 굵게 / 목록 / 문단 정도만 지원하는 작은 마크다운 렌더러 (HTML은 먼저 이스케이프)
function renderMarkdown(md) {
  const blocks = escapeHtml(md).split(/\n{2,}/);
  return blocks.map(block => {
    const lines = block.split("\n");
    const inline = s => s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    if (lines.every(l => /^\s*([-*]|\d+\.)\s+/.test(l))) {
      return "<ul>" + lines.map(l => `<li>${inline(l.replace(/^\s*([-*]|\d+\.)\s+/, ""))}</li>`).join("") + "</ul>";
    }
    return `<p>${lines.map(inline).join("<br>")}</p>`;
  }).join("");
}

function addMsg(cls, html) {
  document.getElementById("empty")?.remove();
  const el = document.createElement("div");
  el.className = `msg ${cls}`;
  el.innerHTML = html;
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
  return el;
}

async function ask(question) {
  input.value = "";
  sendBtn.disabled = true;
  addMsg("user", escapeHtml(question));
  const bot = addMsg("bot typing", "");
  const body = document.createElement("div");
  bot.appendChild(body);
  let answer = "", sources = [];

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, history: history.slice(-6) }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(typeof err.detail === "string" ? err.detail : "요청에 실패했어요.");
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      let idx;
      while ((idx = buf.indexOf("\n\n")) !== -1) {
        const raw = buf.slice(0, idx);
        buf = buf.slice(idx + 2);
        const event = raw.match(/^event: (.*)$/m)?.[1];
        const data = JSON.parse(raw.match(/^data: (.*)$/m)?.[1] ?? "null");
        if (event === "sources") sources = data;
        else if (event === "delta") { answer += data; body.innerHTML = renderMarkdown(answer); }
        else if (event === "error") throw new Error(data);
        log.scrollTop = log.scrollHeight;
      }
    }
    if (sources.length) {
      const box = document.createElement("div");
      box.className = "sources";
      const seen = new Set();
      sources.forEach(s => {
        if (seen.has(s.title)) return;
        seen.add(s.title);
        const tag = document.createElement("span");
        tag.textContent = s.title;
        box.appendChild(tag);
      });
      bot.appendChild(box);
    }
    history.push({ role: "user", content: question }, { role: "assistant", content: answer });
  } catch (e) {
    bot.classList.add("error");
    body.textContent = e.message;
  } finally {
    bot.classList.remove("typing");
    sendBtn.disabled = false;
    input.focus();
    log.scrollTop = log.scrollHeight;
  }
}
