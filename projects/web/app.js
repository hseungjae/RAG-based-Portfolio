const log = document.getElementById("log");
const form = document.getElementById("form");
const input = document.getElementById("q");
const sendBtn = document.getElementById("send");
const resetBtn = document.getElementById("reset");
const themeBtn = document.getElementById("theme");
let history = []; // 최근 대화만 서버에 보내서 후속 질문 맥락으로 사용
const SLOW_MS = 10_000; // 이 시간이 지나도 첫 글자가 없으면 지연 안내를 보여준다
let busy = false;

fetch("/api/config").then(r => r.json()).then(c => {
  document.getElementById("owner").textContent = c.owner;
  document.title = `${c.owner} · Ask Me Anything`;
}).catch(() => {});

/* ---------- 테마: 시스템 → 라이트 → 다크 순서로 전환 ---------- */
const THEMES = ["system", "light", "dark"];
const THEME_LABEL = { system: "시스템 설정", light: "라이트 모드", dark: "다크 모드" };

function currentTheme() {
  return document.documentElement.dataset.theme || "system";
}

function applyTheme(mode) {
  if (mode === "system") delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = mode;
  try {
    if (mode === "system") localStorage.removeItem("theme");
    else localStorage.setItem("theme", mode);
  } catch (e) {}
  themeBtn.dataset.mode = mode;
  const label = `테마: ${THEME_LABEL[mode]} (눌러서 변경)`;
  themeBtn.title = label;
  themeBtn.setAttribute("aria-label", label);
}

applyTheme(currentTheme());
themeBtn.addEventListener("click", () => {
  applyTheme(THEMES[(THEMES.indexOf(currentTheme()) + 1) % THEMES.length]);
});

/* ---------- 입력창 ---------- */
// 빈 입력창에 예시 질문을 돌아가며 보여준다
const PLACEHOLDERS = [
  "기능경기대회 성적은 어땠나요?",
  "어떤 프로젝트를 했나요?",
  "지금 어디서 일하나요?",
  "트러블슈팅 경험이 있나요?",
  "협업 경험을 알려주세요",
  "강점과 약점이 뭐예요?",
];
let placeholderIdx = 0;
if (!matchMedia("(prefers-reduced-motion: reduce)").matches) {
  setInterval(() => {
    if (input.value) return; // 입력 중일 땐 보이지 않으니 바꾸지 않는다
    placeholderIdx = (placeholderIdx + 1) % PLACEHOLDERS.length;
    input.placeholder = PLACEHOLDERS[placeholderIdx];
  }, 3000);
}

function autosize() {
  input.style.height = "auto";
  input.style.height = `${input.scrollHeight}px`;
  // 최대 높이를 넘을 때만 스크롤바를 보여준다
  input.style.overflowY = input.scrollHeight > 140 ? "auto" : "hidden";
}

function updateSend() {
  sendBtn.disabled = busy || !input.value.trim();
}

input.addEventListener("input", () => { autosize(); updateSend(); });
input.addEventListener("keydown", e => {
  // 빈 입력창에서 Tab을 누르면 지금 보이는 예시 질문을 채워 넣는다
  if (e.key === "Tab" && !e.shiftKey && !input.value && !e.isComposing) {
    e.preventDefault();
    input.value = input.placeholder;
    autosize();
    updateSend();
    return;
  }
  // 한글 조합 중 Enter는 무시해야 마지막 글자가 중복 전송되지 않는다
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    form.requestSubmit();
  }
});

form.addEventListener("submit", e => {
  e.preventDefault();
  const q = input.value.trim();
  if (q && !busy) ask(q);
});

document.getElementById("suggest").addEventListener("click", e => {
  // 링크(GitHub, 포트폴리오)는 그대로 열리고, 버튼만 질문으로 보낸다
  const btn = e.target.closest("button");
  if (btn && !busy) ask(btn.dataset.q || btn.textContent);
});

resetBtn.addEventListener("click", () => {
  if (busy) return;
  history = [];
  log.replaceChildren();
  document.body.classList.remove("chatting");
  resetBtn.hidden = true;
  window.scrollTo({ top: 0 });
  input.focus();
});

/* ---------- 메시지 렌더링 ---------- */
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

function scrollToBottom() {
  window.scrollTo({ top: document.body.scrollHeight });
}

function addBlock(cls) {
  const el = document.createElement("div");
  el.className = cls;
  log.appendChild(el);
  scrollToBottom();
  return el;
}


/* ---------- 질문 보내기 ---------- */
async function ask(question) {
  busy = true;
  input.value = "";
  autosize();
  updateSend();
  document.body.classList.add("chatting");
  resetBtn.hidden = false;

  addBlock("q").textContent = question;
  const answerEl = addBlock("a");
  const body = document.createElement("div");
  body.innerHTML = '<span class="thinking" aria-label="답변 작성 중"><i></i><i></i><i></i></span>';
  answerEl.appendChild(body);
  let answer = "";

  // 무료 Gemini API는 붐빌 때 첫 응답까지 수십 초가 걸리기도 해서, 기다리는 이유를 알려준다
  const slowTimer = setTimeout(() => {
    if (answer) return;
    const note = document.createElement("p");
    note.className = "slow-note";
    note.textContent = "답변이 조금 늦어지고 있어요. 무료 AI API(Gemini 무료 플랜)를 사용하고 있어 사용자가 많을 때는 응답이 느려질 수 있어요.";
    body.appendChild(note);
    scrollToBottom();
  }, SLOW_MS);

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
        if (event === "delta") { answer += data; body.innerHTML = renderMarkdown(answer); }
        else if (event === "error") throw new Error(data);
        scrollToBottom();
      }
    }
    history.push({ role: "user", content: question }, { role: "assistant", content: answer });
  } catch (e) {
    answerEl.classList.add("error");
    body.textContent = e.message;
  } finally {
    clearTimeout(slowTimer);
    busy = false;
    updateSend();
    input.focus();
    scrollToBottom();
  }
}
