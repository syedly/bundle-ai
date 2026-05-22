// ── State ──────────────────────────────────────────────────────────────────
let currentRunId  = window.BUNDLE?.currentRunId  || null;
let currentStage  = 1;
let isProcessing  = false;
let selectedTime  = null;
let typingEl      = null;

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
  const el = document.getElementById('messagesScroll');
  if (el) setTimeout(() => { el.scrollTop = el.scrollHeight; }, 60);
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
  avatar.textContent = role === 'ai' ? 'B' : role === 'system' ? '📎' : 'You';

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
  scrollToBottom();
}

// ── Typing Indicator ───────────────────────────────────────────────────────
function showTyping() {
  const scroll = document.getElementById('messagesScroll');
  if (!scroll || typingEl) return;
  typingEl = document.createElement('div');
  typingEl.className = 'typing-indicator';
  typingEl.innerHTML = `
    <div class="msg-avatar" style="background:var(--green-pale);color:var(--green);
      width:32px;height:32px;border-radius:50%;display:flex;align-items:center;
      justify-content:center;font-weight:700;flex-shrink:0;font-size:14px;">B</div>
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
}

// ── Suggestions Bar ────────────────────────────────────────────────────────
function showSuggestions(suggestions) {
  const bar = document.getElementById('suggestionsBar');
  if (!bar) return;
  bar.innerHTML = '';

  if (!suggestions || suggestions.length === 0) {
    bar.style.display = 'none';
    return;
  }

  bar.style.display = 'flex';
  suggestions.forEach(text => {
    if (!text.trim()) return;
    const btn = document.createElement('button');
    btn.className = 'sug-btn';
    btn.textContent = text;
    btn.onclick = () => {
      hideSuggestions();
      sendMessage(text);
    };
    bar.appendChild(btn);
  });
}

function hideSuggestions() {
  const bar = document.getElementById('suggestionsBar');
  if (bar) { bar.innerHTML = ''; bar.style.display = 'none'; }
  removeSessionCards();
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
    { n: 10, desc: 'Comprehensive transformation — max ROI',                 rec: false },
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

// ── Handle AI response (suggestions + stage-specific UI) ──────────────────
function handleAiResponse(data) {
  removeTyping();
  appendMessage('ai', data.message);
  updateStageUI(data.stage);

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

  // Decide what to show below the message (skip if plan actions shown)
  if (data.status !== 'plan_generated') {
    const aiLower = (data.message || '').toLowerCase();

    if (/how many sessions|number of sessions/.test(aiLower)) {
      showSessionCards();
      hideSuggestions();
    } else if (data.suggestions && data.suggestions.length > 0) {
      showSuggestions(data.suggestions);
    } else {
      hideSuggestions();
    }
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
  if (window.BUNDLE?.isLocked) return;

  document.getElementById('welcomeScreen').style.display   = 'none';
  document.getElementById('messagesContainer').style.display = '';
  document.getElementById('inputArea').style.display        = '';

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
      document.getElementById('messagesContainer').style.display = 'none';
      document.getElementById('inputArea').style.display         = 'none';
      document.getElementById('welcomeScreen').style.display     = '';
      return;
    }

    if (!res.ok) throw new Error(data.error || 'Failed to start');

    currentRunId = data.run_id;
    sessionStorage.setItem('run_id', String(currentRunId));
    updateStageUI(data.stage || 1);

    // Update free meter
    updateFreeMeter(data.runs_used, data.free_limit);

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
  showTyping();
  isProcessing = true;

  const sendBtn = document.getElementById('sendBtn');
  if (sendBtn) sendBtn.disabled = true;

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
    if (sendBtn) sendBtn.disabled = false;
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

  const sendBtn = document.getElementById('sendBtn');
  if (sendBtn) sendBtn.disabled = true;

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
    if (sendBtn) sendBtn.disabled = false;
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

    // Show chat area
    document.getElementById('welcomeScreen').style.display    = 'none';
    document.getElementById('messagesContainer').style.display = '';
    document.getElementById('inputArea').style.display         = '';
    document.getElementById('bookingFormWrap').style.display   = 'none';

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

    // Show plan action buttons if plan was already generated
    removePlanActions();
    if (data.status === 'plan_generated' || data.status === 'cta_clicked') {
      showPlanActions();
    }

    // Highlight active thread in sidebar
    document.querySelectorAll('.thread-item').forEach(el => el.classList.remove('active'));
    const el = document.querySelector(`.thread-item[data-run-id="${runId}"]`);
    if (el) el.classList.add('active');

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

// ── New Run ────────────────────────────────────────────────────────────────
function confirmNewRun() {
  if (currentRunId && !confirm('Start a new training plan? Your current conversation is saved.')) return;
  sessionStorage.removeItem('run_id');
  window.location.reload();
}

// ── On Page Load ───────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  // If locked, nothing to do
  if (window.BUNDLE?.isLocked) return;

  try {
    const res  = await fetch('/api/start/');
    const data = await res.json();

    if (data.type === 'unauthenticated') {
      window.location.href = '/login/';
      return;
    }

    if (data.type === 'resume' && data.history?.length > 0) {
      document.getElementById('welcomeScreen').style.display    = 'none';
      document.getElementById('messagesContainer').style.display = '';
      document.getElementById('inputArea').style.display         = '';

      currentRunId = data.run_id;
      sessionStorage.setItem('run_id', String(currentRunId));
      updateStageUI(data.stage || 1);

      let lastAi = '';
      for (const msg of data.history) {
        const role = msg.role === 'user' ? 'user' : 'ai';
        appendMessage(role, msg.content, false);
        if (role === 'ai') lastAi = msg.content;
      }

      if (data.stage === 6) {
        const wrap = document.getElementById('bookingFormWrap');
        if (wrap) {
          wrap.style.display = '';
          const di = document.getElementById('bookDate');
          if (di) di.min = new Date().toISOString().split('T')[0];
        }
      }

      // Show plan action buttons if plan was already generated
      if (data.status === 'plan_generated' || data.status === 'cta_clicked') {
        showPlanActions();
      }

      // Highlight active thread
      const el = document.querySelector(`.thread-item[data-run-id="${data.run_id}"]`);
      if (el) el.classList.add('active');
    }
    // else: welcome screen is shown by default

  } catch (err) {
    console.warn('Session check failed:', err);
  }
});
