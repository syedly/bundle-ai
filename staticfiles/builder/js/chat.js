// ── State ──────────────────────────────────────────────────────────────────
let currentRunId       = window.BUNDLE?.currentRunId  || null;
let currentStage       = 1;
let isProcessing       = false;
let selectedTime       = null;
let typingEl           = null;
let generatingEl       = null;
let generatingInterval = null;

// ── Multi-step generating animation ───────────────────────────────────────
const GENERATING_STEPS = {
  recommendation: [
    'Reading your inputs',
    'Identifying growth opportunities',
    'Generating your recommendation',
    'Checking the pathway',
    'Polishing the recommendation',
  ],
  plan: [
    'Reading your inputs',
    'Selecting sessions for your learner',
    'Building the per-learner plan',
    'Adding coaching context',
    'Finalising your plan',
  ],
};

function _generatingType(text) {
  const t = (text || '').toLowerCase();
  if (/generat.*recommendation|put.*recommendation|go ahead.*generat|recommendation.*together/.test(t))
    return 'recommendation';
  if (/draft.*plan|per.learner|generat.*plan|create.*plan|build.*plan|all set.*draft|go ahead.*draft/.test(t))
    return 'plan';
  return null;
}

function showGeneratingSteps(type) {
  const scroll = document.getElementById('messagesScroll');
  if (!scroll) return;
  removeGeneratingSteps();
  removeTyping();

  const steps = GENERATING_STEPS[type] || GENERATING_STEPS.recommendation;
  let idx = 0;

  generatingEl = document.createElement('div');
  generatingEl.className = 'message ai';

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = 'b';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble generating-bubble';
  bubble.innerHTML = `<span class="gen-step">${steps[0]}</span>`;

  generatingEl.appendChild(avatar);
  generatingEl.appendChild(bubble);
  scroll.appendChild(generatingEl);
  scrollToBottom();

  generatingInterval = setInterval(() => {
    idx = (idx + 1) % steps.length;
    const el = bubble.querySelector('.gen-step');
    if (!el) return;
    el.style.opacity = '0';
    setTimeout(() => {
      el.textContent = steps[idx];
      el.style.opacity = '1';
    }, 220);
  }, 1400);
}

function removeGeneratingSteps() {
  if (generatingInterval) { clearInterval(generatingInterval); generatingInterval = null; }
  if (generatingEl?.parentNode) generatingEl.parentNode.removeChild(generatingEl);
  generatingEl = null;
}

// ── Markdown Renderer ──────────────────────────────────────────────────────
function renderMarkdown(text) {
  if (!text) return '';
  let s = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  const lines = s.split('\n');
  const out = [];
  let inList = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (isTableHeader(lines, i)) {
      if (inList) { out.push('</ul>'); inList = false; }
      const headers = tableCells(line);
      const rows = [];
      i += 2;
      while (i < lines.length && /\|/.test(lines[i]) && lines[i].trim() !== '') {
        rows.push(tableCells(lines[i]));
        i++;
      }
      i--;
      out.push(renderTable(headers, rows));
      continue;
    }
    if (/^-{3,}$/.test(line.trim())) {
      if (inList) { out.push('</ul>'); inList = false; }
      out.push('<hr>'); continue;
    }
    if (/^# /.test(line)) {
      if (inList) { out.push('</ul>'); inList = false; }
      out.push(`<h1>${inl(line.slice(2))}</h1>`); continue;
    }
    if (/^## /.test(line)) {
      if (inList) { out.push('</ul>'); inList = false; }
      out.push(`<h2>${inl(line.slice(3))}</h2>`); continue;
    }
    if (/^### /.test(line)) {
      if (inList) { out.push('</ul>'); inList = false; }
      out.push(`<h3>${inl(line.slice(4))}</h3>`); continue;
    }
    if (/^#### /.test(line)) {
      if (inList) { out.push('</ul>'); inList = false; }
      out.push(`<h4>${inl(line.slice(5))}</h4>`); continue;
    }
    if (/^[-*] /.test(line)) {
      if (!inList) { out.push('<ul>'); inList = true; }
      out.push(`<li>${inl(line.slice(2))}</li>`); continue;
    }
    if (line.trim() === '') {
      if (inList) { out.push('</ul>'); inList = false; }
      continue;
    }
    if (inList) { out.push('</ul>'); inList = false; }
    out.push(`<p>${inl(line)}</p>`);
  }
  if (inList) out.push('</ul>');
  return out.join('');
}

function isTableHeader(lines, i) {
  return i + 1 < lines.length && /\|/.test(lines[i]) && /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(lines[i + 1]);
}

function tableCells(line) {
  return line.replace(/^\s*\|/, '').replace(/\|\s*$/, '').split('|').map(c => c.trim());
}

function renderTable(headers, rows) {
  const head = headers.map(h => `<th>${inl(h)}</th>`).join('');
  const body = rows.map(row => `<tr>${row.map(c => `<td>${inl(c)}</td>`).join('')}</tr>`).join('');
  return `<div class="md-table-wrap"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}

function inl(t) {
  return t
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,     '<em>$1</em>')
    .replace(/`(.+?)`/g,       '<code>$1</code>')
    .replace(/&lt;br\s*\/?&gt;/gi, '<br>');
}

// ── CSRF ───────────────────────────────────────────────────────────────────
function getCsrf() {
  const c = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
  return c ? c.split('=')[1] : '';
}

// ── Scroll ─────────────────────────────────────────────────────────────────
function scrollToBottom() {
  setTimeout(() => {
    const el = document.getElementById('messagesScroll');
    if (el && el.scrollHeight > el.clientHeight) {
      el.scrollTop = el.scrollHeight;
    }
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
  }, 60);
}

// ── Stage UI ───────────────────────────────────────────────────────────────
function updateStageUI(stage) {
  if (!stage) return;
  currentStage = stage;
  document.querySelectorAll('.stage-dot').forEach(d => {
    const s = +d.dataset.stage;
    d.classList.toggle('active',    s === stage);
    d.classList.toggle('completed', s < stage);
  });
  document.querySelectorAll('.progress-item').forEach(d => {
    const s = +d.dataset.stage;
    d.classList.toggle('active',    s === stage);
    d.classList.toggle('completed', s < stage);
  });
  updateChatProgress();
}

const PROGRESS_TOTAL = 15;

function updateChatProgress() {
  const label = document.querySelector('.chat-progress-label');
  const fill  = document.querySelector('.chat-progress-fill');
  const scroll = document.getElementById('messagesScroll');

  let questionNum = 1;
  if (scroll) {
    const userAnswers = scroll.querySelectorAll('.message.user').length;
    questionNum = Math.min(Math.max(userAnswers + 1, 1), PROGRESS_TOTAL);
  }

  if (currentStage >= 5) questionNum = PROGRESS_TOTAL;
  else if (currentStage >= 4) questionNum = Math.max(questionNum, 12);

  const pct = Math.min((questionNum / PROGRESS_TOTAL) * 100, 100);
  if (label) label.textContent = `${questionNum} of ~${PROGRESS_TOTAL} questions`;
  if (fill) fill.style.width = `${pct}%`;
}

// ── Append Message ─────────────────────────────────────────────────────────
function appendMessage(role, content, animate = true) {
  const scroll = document.getElementById('messagesScroll');
  if (!scroll) return;

  const wrap   = document.createElement('div');
  wrap.className = `message ${role}`;
  if (!animate) { wrap.style.animation = 'none'; wrap.style.opacity = '1'; }

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = role === 'ai' ? 'b' : role === 'system' ? '📎' : 'You';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  if (role === 'ai' && /^#\s/m.test(content || '')) {
    bubble.classList.add('generated-doc');
  }
  if (role === 'ai') {
    bubble.innerHTML = renderMarkdown(content);
  } else {
    bubble.textContent = content;
  }

  wrap.appendChild(avatar);
  wrap.appendChild(bubble);
  scroll.appendChild(wrap);
  if (role === 'user') updateChatProgress();
  scrollToBottom();
}

// ── Typing Indicator ───────────────────────────────────────────────────────
function showTyping() {
  const scroll = document.getElementById('messagesScroll');
  if (!scroll || typingEl) return;
  typingEl = document.createElement('div');
  typingEl.className = 'typing-indicator';
  typingEl.innerHTML = `
    <div class="msg-avatar">b</div>
    <div class="typing-bubble">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>`;
  scroll.appendChild(typingEl);
  scrollToBottom();
}

function removeTyping() {
  if (typingEl?.parentNode) typingEl.parentNode.removeChild(typingEl);
  typingEl = null;
  removeGeneratingSteps();
}

// ── Suggestions Bar ────────────────────────────────────────────────────────
const SUGGESTIONS_SPARKLE_SVG = `<svg class="suggestions-sparkle" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
  <path d="M12 3l1.2 4.2L17 8.5l-3.8 1.3L12 14l-1.2-4.2L7 8.5l3.8-1.3L12 3z"></path>
  <path d="M5 16l.8 2.8L8.5 20l-2.7.9L5 24l-.8-3.1L1.5 20l2.7-.9L5 16z"></path>
  <path d="M19 14l.8 2.8L22.5 18l-2.7.9L19 22l-.8-3.1L15.5 18l2.7-.9L19 14z"></path>
</svg>`;

function showSuggestions(suggestions) {
  const bar = document.getElementById('suggestionsBar');
  if (!bar) return;
  bar.innerHTML = '';
  bar.classList.remove('is-visible');

  const items = normalizeSuggestions(suggestions);
  if (!items.length) return;

  const header = document.createElement('div');
  header.className = 'suggestions-header';
  header.innerHTML = `${SUGGESTIONS_SPARKLE_SVG}<span class="suggestions-label">Quick replies</span>`; /* styled uppercase in CSS */

  const buttons = document.createElement('div');
  buttons.className = 'suggestions-buttons';

  items.forEach(text => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'sug-btn';
    btn.textContent = text;
    btn.onclick = () => {
      if (isProcessing) return;
      sendMessage(text);
    };
    buttons.appendChild(btn);
  });

  if (!buttons.children.length) return;

  const hint = document.createElement('p');
  hint.className = 'suggestions-hint';
  hint.textContent = 'Tap an option to send, or type your own answer below.';

  bar.appendChild(header);
  bar.appendChild(buttons);
  bar.appendChild(hint);
  bar.removeAttribute('style');
  bar.classList.add('is-visible');
}

function hideSuggestions() {
  const bar = document.getElementById('suggestionsBar');
  if (bar) {
    bar.innerHTML = '';
    bar.classList.remove('is-visible');
  }
  removeSessionCards();
}

function normalizeSuggestions(raw) {
  if (!raw) return [];
  if (Array.isArray(raw)) {
    return raw.map(s => String(s).trim()).filter(Boolean);
  }
  if (typeof raw === 'string') {
    return raw.split('|').map(s => s.trim()).filter(Boolean);
  }
  return [];
}

function showSuggestionsFromResponse(data, lastAiText) {
  if (data.status === 'plan_generated') return;
  const aiLower = (lastAiText || data.message || '').toLowerCase();
  if (/how many sessions|number of sessions/.test(aiLower)) {
    showSessionCards();
    hideSuggestions();
    return;
  }
  const items = normalizeSuggestions(data.suggestions);
  if (items.length > 0) {
    showSuggestions(items);
  } else {
    hideSuggestions();
  }
}

// ── Session Count Cards ────────────────────────────────────────────────────
function showSessionCards() {
  const scroll = document.getElementById('messagesScroll');
  if (!scroll) return;
  removeSessionCards();

  const wrap = document.createElement('div');
  wrap.id = 'sessionCardsWrap';
  wrap.className = 'session-cards';

  [
    { n: 4,  desc: 'Quick start, high-focus intervention',                  rec: false },
    { n: 6,  desc: 'Balanced depth — most common starting point',            rec: false },
    { n: 8,  desc: "Full behavior change — Bundle's recommended minimum",    rec: true  },
  ].forEach(c => {
    const card = document.createElement('div');
    card.className = 'sc-card' + (c.rec ? ' recommended' : '');
    card.innerHTML = `
      <div class="sc-number">${c.n}</div>
      <div class="sc-label">sessions</div>
      <div class="sc-desc">${c.desc}</div>
      ${c.rec ? '<div class="sc-rec">Recommended</div>' : ''}`;
    card.onclick = () => { removeSessionCards(); sendMessage(`${c.n} sessions`); };
    wrap.appendChild(card);
  });

  scroll.appendChild(wrap);
  scrollToBottom();
}

function removeSessionCards() {
  document.getElementById('sessionCardsWrap')?.remove();
}

// ── Plan Action Buttons ────────────────────────────────────────────────────
function showPlanActions() {
  if (document.getElementById('planActionsWrap')) return; // already shown
  const scroll = document.getElementById('messagesScroll');
  if (!scroll || !currentRunId) return;

  const wrap = document.createElement('div');
  wrap.id = 'planActionsWrap';
  wrap.className = 'plan-actions';

  const dlBtn = document.createElement('a');
  dlBtn.href = `/api/pdf/${currentRunId}/`;
  dlBtn.className = 'btn-plan-action btn-download-pdf';
  dlBtn.innerHTML = '⬇&nbsp; Download Training Plan (PDF)';
  dlBtn.target = '_blank';
  dlBtn.rel = 'noopener';

  const bookBtn = document.createElement('button');
  bookBtn.className = 'btn-plan-action btn-book-consultation';
  bookBtn.innerHTML = '📅&nbsp; Book a Consultation';
  bookBtn.onclick = () => {
    const wrap = document.getElementById('bookingFormWrap');
    if (wrap) {
      wrap.style.display = '';
      wrap.scrollIntoView({ behavior: 'smooth', block: 'start' });
      const di = document.getElementById('bookDate');
      if (di && !di.min) di.min = new Date().toISOString().split('T')[0];
    }
  };

  wrap.appendChild(dlBtn);
  wrap.appendChild(bookBtn);
  scroll.appendChild(wrap);
  scrollToBottom();
}

function removePlanActions() {
  document.getElementById('planActionsWrap')?.remove();
}

function removeReportActions() {
  document.getElementById('reportActionsWrap')?.remove();
}

function showReportActions(data) {
  if (!currentRunId) return;
  removeReportActions();

  const hasAnalysis = data.has_analysis_report;
  const hasPlan = data.has_final_plan_report;
  if (!hasAnalysis && !hasPlan) return;

  const scroll = document.getElementById('messagesScroll');
  if (!scroll) return;

  const wrap = document.createElement('div');
  wrap.id = 'reportActionsWrap';
  wrap.className = 'report-actions';

  if (hasAnalysis) {
    const a = document.createElement('a');
    a.href = `/chat/${currentRunId}/report/analysis/`;
    a.className = 'btn-report-action btn-report-analysis';
    a.target = '_blank';
    a.rel = 'noopener';
    a.innerHTML = '📊&nbsp; View AI Analysis Report';
    wrap.appendChild(a);
  }

  if (hasPlan) {
    const p = document.createElement('a');
    p.href = `/chat/${currentRunId}/report/plan/`;
    p.className = 'btn-report-action btn-report-plan';
    p.target = '_blank';
    p.rel = 'noopener';
    p.innerHTML = '📋&nbsp; View Learning Plan Report';
    wrap.appendChild(p);
  }

  scroll.appendChild(wrap);
  scrollToBottom();
}

// ── Handle AI response (suggestions + stage-specific UI) ──────────────────
function handleAiResponse(data) {
  removeTyping();
  appendMessage('ai', data.message);
  updateStageUI(data.stage);
  showReportActions(data);

  // Show plan action buttons when plan is generated
  if (data.status === 'plan_generated') {
    removePlanActions();
    showPlanActions();
    hideSuggestions();
    removeSessionCards();
  }

  // Show booking form when stage 6
  if (data.stage === 6) {
    const wrap = document.getElementById('bookingFormWrap');
    if (wrap) {
      wrap.style.display = '';
      const di = document.getElementById('bookDate');
      if (di && !di.min) di.min = new Date().toISOString().split('T')[0];
    }
  }

  if (data.status !== 'plan_generated') {
    showSuggestionsFromResponse(data, data.message);
  }

  // Update thread title in sidebar if we have it
  if (data.run_id) {
    document.querySelectorAll(`.thread-item`).forEach(el => el.classList.remove('active'));
    const el = document.querySelector(`.thread-item[data-run-id="${data.run_id}"]`);
    if (el) el.classList.add('active');
  }
}

// ── Start New Chat ─────────────────────────────────────────────────────────
async function startChat() {
  if (window.BUNDLE?.isLocked) {
    window.location.href = '/';
    return;
  }

  const scroll = document.getElementById('messagesScroll');
  if (scroll) scroll.innerHTML = '';
  hideSuggestions();
  updateSendButton();
  showTyping();

  try {
    const res  = await fetch('/api/new/', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCsrf(), 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    const data = await res.json();

    if (res.status === 403 && data.error === 'free_limit_reached') {
      removeTyping();
      window.location.href = '/';
      return;
    }

    if (!res.ok) throw new Error(data.error || 'Failed to start');

    currentRunId = data.run_id;
    sessionStorage.setItem('run_id', String(currentRunId));
    if (window.BUNDLE?.chatMode === 'new') {
      window.history.replaceState(null, '', `/chat/${currentRunId}/`);
      window.BUNDLE.chatMode = 'thread';
      window.BUNDLE.runId = currentRunId;
    }
    updateStageUI(data.stage || 1);
    handleAiResponse(data);

  } catch (err) {
    removeTyping();
    appendMessage('ai', 'Something went wrong getting started. Please refresh and try again.');
  }
}

// ── Send Message ───────────────────────────────────────────────────────────
async function sendMessage(overrideText) {
  if (isProcessing) return;

  const input = document.getElementById('messageInput');
  const text  = overrideText || input?.value.trim();
  if (!text || !currentRunId) return;

  if (!overrideText && input) { input.value = ''; input.style.height = 'auto'; }

  hideSuggestions();
  appendMessage('user', text);

  // Show multi-step animation for recommendation/plan generation; plain dots otherwise
  const genType = _generatingType(text);
  if (genType) {
    showGeneratingSteps(genType);
  } else {
    showTyping();
  }
  isProcessing = true;

  updateSendButton();

  try {
    const res  = await fetch('/api/chat/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body: JSON.stringify({ message: text, run_id: currentRunId }),
    });
    const data = await res.json();

    if (!res.ok) {
      removeTyping();
      if (data.reset) {
        sessionStorage.removeItem('run_id');
        currentRunId = null;
      }
      appendMessage('ai', data.error || 'Something went wrong. Please try again.');
      return;
    }

    handleAiResponse(data);

  } catch {
    removeTyping();
    appendMessage('ai', 'Something went wrong. Please try again.');
  } finally {
    isProcessing = false;
    updateSendButton();
    if (!overrideText && input) input.focus();
  }
}

// ── File Upload ────────────────────────────────────────────────────────────
async function uploadFile(input) {
  const file = input.files[0];
  if (!file || !currentRunId) { input.value = ''; return; }

  const hint = document.getElementById('fileUploadHint');
  const hintText = document.getElementById('fileUploadHintText');

  // Show hint
  if (hint && hintText) {
    hintText.textContent = `Uploading ${file.name}…`;
    hint.style.display = 'flex';
  }

  const fd = new FormData();
  fd.append('file', file);

  hideSuggestions();
  showTyping();
  isProcessing = true;

  updateSendButton();

  try {
    const res  = await fetch(`/api/upload/${currentRunId}/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCsrf() },
      body: fd,
    });
    const data = await res.json();

    if (hint) hint.style.display = 'none';

    if (!res.ok) {
      removeTyping();
      appendMessage('ai', data.error || 'Could not process that file. Please try again.');
      return;
    }

    // Show a system-style "file uploaded" bubble
    appendMessage('system', data.display_message, true);
    handleAiResponse(data);

  } catch {
    removeTyping();
    if (hint) hint.style.display = 'none';
    appendMessage('ai', 'File upload failed. Please try again.');
  } finally {
    isProcessing = false;
    updateSendButton();
    input.value = '';
  }
}

// ── Load Thread ────────────────────────────────────────────────────────────
async function loadThread(runId) {
  if (isProcessing) return;

  try {
    const res  = await fetch(`/threads/load/${runId}/`);
    const data = await res.json();
    if (!res.ok) return;

    currentRunId = data.run_id;
    sessionStorage.setItem('run_id', String(currentRunId));

    const bookingWrap = document.getElementById('bookingFormWrap');
    if (bookingWrap) bookingWrap.style.display = 'none';

    // Clear and replay
    const scroll = document.getElementById('messagesScroll');
    if (scroll) scroll.innerHTML = '';
    hideSuggestions();

    let lastAi = '';
    for (const msg of (data.history || [])) {
      const role = msg.role === 'user' ? 'user' : 'ai';
      appendMessage(role, msg.content, false);
      if (role === 'ai') lastAi = msg.content;
    }

    updateStageUI(data.stage || 1);

    if (data.stage === 6) {
      const wrap = document.getElementById('bookingFormWrap');
      if (wrap) {
        wrap.style.display = '';
        const di = document.getElementById('bookDate');
        if (di) di.min = new Date().toISOString().split('T')[0];
      }
    }

    removePlanActions();
    removeReportActions();
    showReportActions(data);

    if (data.status === 'plan_generated' || data.status === 'cta_clicked') {
      showPlanActions();
      hideSuggestions();
    } else {
      showSuggestionsFromResponse(data, lastAi);
    }

    updateChatProgress();
    updateSendButton();

  } catch (err) {
    console.error('loadThread error:', err);
  }
}

// ── Free Meter ─────────────────────────────────────────────────────────────
function updateFreeMeter(used, limit) {
  const fill  = document.getElementById('freeMeterFill');
  const label = document.getElementById('freeMeterLabel');
  if (fill)  fill.style.width  = `${Math.min((used / limit) * 100, 100)}%`;
  if (label) label.textContent = `${used}/${limit} used`;
}

// ── Keyboard ───────────────────────────────────────────────────────────────
function handleKeyDown(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function updateSendButton() {
  const input = document.getElementById('messageInput');
  const btn   = document.getElementById('sendBtn');
  if (!btn) return;
  const hasText = !!(input?.value.trim());
  btn.disabled = !hasText || isProcessing;
  btn.classList.toggle('btn-send--inactive', !hasText || isProcessing);
}

// ── Booking ────────────────────────────────────────────────────────────────
function selectTime(btn, time) {
  document.querySelectorAll('.time-slot').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  selectedTime = time;
  checkBookingForm();
}

function checkBookingForm() {
  const ok = ['bookName','bookEmail','bookPhone','bookDate'].every(
    id => document.getElementById(id)?.value.trim()
  ) && selectedTime;
  const btn = document.getElementById('bookBtn');
  if (btn) btn.disabled = !ok;
}

async function submitBooking() {
  if (!currentRunId) return;
  const btn = document.getElementById('bookBtn');
  if (btn) { btn.disabled = true; btn.textContent = 'Booking…'; }

  try {
    const res  = await fetch(`/api/book/${currentRunId}/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body: JSON.stringify({
        name:  document.getElementById('bookName')?.value.trim(),
        email: document.getElementById('bookEmail')?.value.trim(),
        phone: document.getElementById('bookPhone')?.value.trim(),
        date:  document.getElementById('bookDate')?.value,
        time:  selectedTime,
      }),
    });
    const data = await res.json();
    if (data.success && data.redirect) {
      sessionStorage.removeItem('run_id');
      window.location.href = data.redirect;
    } else {
      if (btn) { btn.disabled = false; btn.textContent = 'Book My Consultation'; }
      appendMessage('ai', 'There was an issue saving your booking. Please try again.');
    }
  } catch {
    if (btn) { btn.disabled = false; btn.textContent = 'Book My Consultation'; }
    appendMessage('ai', 'Something went wrong. Please try again.');
  }
}

// ── On Page Load (chat page only) ───────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const mode = window.BUNDLE?.chatMode;
  if (!mode) return;

  if (mode === 'new' && window.BUNDLE.isLocked) {
    window.location.href = '/';
    return;
  }

  updateSendButton();
  updateChatProgress();

  if (mode === 'new') {
    startChat();
  } else if (mode === 'thread' && window.BUNDLE.runId) {
    loadThread(window.BUNDLE.runId);
  }
});
