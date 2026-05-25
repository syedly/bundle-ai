/* ── Bundle AI — Prompt Admin JS ────────────────────────────────────────────── */

(function () {
  'use strict';

  // ── Live word / char / line counter for the prompt textarea ────────────────

  function attachCounter(textarea) {
    // Create the counter bar
    const bar = document.createElement('div');
    bar.className = 'prompt-wordcount-bar';
    bar.innerHTML = (
      '<span class="wc-chars">0 chars</span>' +
      '<span class="wc-words">0 words</span>' +
      '<span class="wc-lines">0 lines</span>' +
      '<span class="wc-tip" style="margin-left:auto;opacity:0.6">Ctrl+A to select all</span>'
    );

    // Insert right after textarea
    textarea.parentNode.insertBefore(bar, textarea.nextSibling);

    const charsEl = bar.querySelector('.wc-chars');
    const wordsEl = bar.querySelector('.wc-words');
    const linesEl = bar.querySelector('.wc-lines');

    function update() {
      const text   = textarea.value;
      const chars  = text.length;
      const words  = text.trim() ? text.trim().split(/\s+/).length : 0;
      const lines  = text.split('\n').length;

      charsEl.textContent = chars.toLocaleString() + ' chars';
      wordsEl.textContent = words.toLocaleString() + ' words';
      linesEl.textContent = lines.toLocaleString() + ' lines';

      // Colour chars red if very large
      charsEl.style.color = chars > 5000 ? '#f38ba8' : chars > 2000 ? '#fab387' : '#89b4fa';
    }

    textarea.addEventListener('input', update);
    update(); // initial count
  }

  // ── Tab key → insert 2 spaces (not focus-jump) ─────────────────────────────

  function attachTabKey(textarea) {
    textarea.addEventListener('keydown', function (e) {
      if (e.key === 'Tab') {
        e.preventDefault();
        const start = this.selectionStart;
        const end   = this.selectionEnd;
        this.value  = this.value.slice(0, start) + '  ' + this.value.slice(end);
        this.selectionStart = this.selectionEnd = start + 2;
      }
    });
  }

  // ── Unsaved-changes warning ─────────────────────────────────────────────────

  function attachUnsavedWarning(textarea) {
    let originalValue = textarea.value;
    let dirty = false;

    textarea.addEventListener('input', function () {
      dirty = (this.value !== originalValue);
    });

    window.addEventListener('beforeunload', function (e) {
      if (dirty) {
        e.preventDefault();
        e.returnValue = '';
      }
    });

    // Clear dirty flag when the form is submitted
    const form = textarea.closest('form');
    if (form) {
      form.addEventListener('submit', function () { dirty = false; });
    }
  }

  // ── Confirm before reverting ─────────────────────────────────────────────────

  function attachRevertConfirm() {
    document.querySelectorAll('a[href*="revert_version="]').forEach(function (link) {
      link.addEventListener('click', function (e) {
        const ts = link.href.match(/revert_version=(\d+)/);
        const msg = ts
          ? 'Revert to this older version? The current content will be saved as a new version first.'
          : 'Revert to this version?';
        if (!confirm(msg)) {
          e.preventDefault();
        }
      });
    });
  }

  // ── Auto-expand textarea height on load ─────────────────────────────────────

  function autoExpand(textarea) {
    textarea.style.height = 'auto';
    const h = Math.max(400, Math.min(textarea.scrollHeight, 900));
    textarea.style.height = h + 'px';
  }

  // ── Init ────────────────────────────────────────────────────────────────────

  function init() {
    document.querySelectorAll('.prompt-editor-textarea').forEach(function (ta) {
      attachCounter(ta);
      attachTabKey(ta);
      attachUnsavedWarning(ta);
      autoExpand(ta);
    });

    attachRevertConfirm();

    // Show a notice if we arrived via revert_version param
    const params = new URLSearchParams(window.location.search);
    if (params.has('revert_version')) {
      const notice = document.createElement('div');
      notice.className = 'save-version-notice';
      notice.textContent = (
        '↩ Content reverted from an older version. '
        + 'Review the content below and click Save to confirm.'
      );
      const firstFieldset = document.querySelector('.module');
      if (firstFieldset) {
        firstFieldset.parentNode.insertBefore(notice, firstFieldset);
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
