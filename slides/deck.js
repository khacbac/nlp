// Minimal slide runtime: scale, keyboard navigation, footer, speaker notes, presenter window, overview.
(function () {
  const stage = document.getElementById('stage');
  const slides = Array.from(stage.querySelectorAll('section.slide'));
  const total = slides.length;
  const isPresenter = new URLSearchParams(location.search).has('presenter');
  const channel = 'BroadcastChannel' in window ? new BroadcastChannel('nlp-deck') : null;
  let current = 0;

  // Footer: section label (from the latest divider's data-part) on the left, page number on the right.
  let part = '';
  slides.forEach((s, i) => {
    if (s.dataset.part) part = s.dataset.part;
    if (s.classList.contains('nofoot')) return;
    const foot = document.createElement('div');
    foot.className = 'foot';
    foot.innerHTML = `<span>${s.classList.contains('divider') ? '' : part}</span><span>${i + 1} / ${total}</span>`;
    s.appendChild(foot);
    const bar = document.createElement('div');
    bar.className = 'progress';
    bar.style.width = `${((i + 1) / total) * 100}%`;
    s.appendChild(bar);
  });

  // Table of contents page numbers: <span data-goto="slide-id">.
  document.querySelectorAll('[data-pageof]').forEach(el => {
    const idx = slides.findIndex(s => s.id === el.dataset.pageof);
    if (idx >= 0) el.textContent = `tr. ${idx + 1}`;
  });

  function fit() {
    if (document.body.classList.contains('overview')) return;
    const k = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
    // Stage sits at 50%/50%; shift back by half its own size, then scale around its center.
    stage.style.transform = `translate(-50%, -50%) scale(${k})`;
    stage.style.transformOrigin = 'center center';
  }

  const notesBox = document.getElementById('notes');
  function renderNotes() {
    const s = slides[current];
    const n = s.querySelector('aside.notes');
    const next = slides[current + 1];
    const nextTitle = next ? (next.querySelector('h1,h2')?.textContent || next.id) : '— hết —';
    notesBox.innerHTML = `<div class="meta">Slide ${current + 1}/${total} · tiếp theo: ${nextTitle}</div>${n ? n.innerHTML : '<i>(không có ghi chú)</i>'}`;
  }

  function show(i, fromRemote) {
    i = Math.max(0, Math.min(total - 1, i));
    slides[current].classList.remove('active');
    current = i;
    const s = slides[current];
    s.classList.add('active');
    // restart entrance animations
    s.querySelectorAll('.rise').forEach(el => { el.style.animation = 'none'; void el.offsetWidth; el.style.animation = ''; });
    history.replaceState(null, '', `${location.search}#${current + 1}`);
    renderNotes();
    if (channel && !fromRemote) channel.postMessage({ slide: current });
    if (isPresenter) renderPresenter();
  }

  function toggleOverview() {
    document.body.classList.toggle('overview');
    if (document.body.classList.contains('overview')) {
      stage.style.transform = '';
      slides[current].scrollIntoView({ block: 'center' });
    } else fit();
  }

  document.addEventListener('keydown', e => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const k = e.key;
    if (['ArrowRight', 'ArrowDown', 'PageDown', ' ', 'Enter'].includes(k)) { e.preventDefault(); show(current + 1); }
    else if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace'].includes(k)) { e.preventDefault(); show(current - 1); }
    else if (k === 'Home') show(0);
    else if (k === 'End') show(total - 1);
    else if (k === 'n' || k === 'N') notesBox.classList.toggle('on');
    else if (k === 'o' || k === 'O' || k === 'Escape') { if (k !== 'Escape' || document.body.classList.contains('overview')) toggleOverview(); }
    else if (k === 'f' || k === 'F') { document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen(); }
    else if (k === 'p' || k === 'P') window.open(`${location.pathname}?presenter#${current + 1}`, 'presenter', 'width=1200,height=800');
  });
  stage.addEventListener('click', e => {
    const s = e.target.closest('section.slide');
    if (document.body.classList.contains('overview') && s) { toggleOverview(); show(slides.indexOf(s)); }
  });
  if (channel) channel.onmessage = ev => { if (typeof ev.data?.slide === 'number') show(ev.data.slide, true); };
  window.addEventListener('resize', fit);
  window.addEventListener('hashchange', () => { const h = parseInt(location.hash.slice(1), 10); if (h && h - 1 !== current) show(h - 1); });

  // Presenter view: notes large, current slide small, timer.
  let t0 = Date.now();
  function renderPresenter() {
    const pv = document.getElementById('presenter');
    const s = slides[current];
    const n = s.querySelector('aside.notes');
    const next = slides[current + 1];
    pv.querySelector('.p-title').textContent = `${current + 1}/${total} · ${s.querySelector('h1,h2')?.textContent || s.id}`;
    pv.querySelector('.p-next').textContent = next ? `Tiếp: ${next.querySelector('h1,h2')?.textContent || next.id}` : 'Slide cuối';
    pv.querySelector('.p-notes').innerHTML = n ? n.innerHTML : '<i>(không có ghi chú)</i>';
  }
  if (isPresenter) {
    document.body.classList.add('presenter-mode');
    const pv = document.createElement('div');
    pv.id = 'presenter';
    pv.innerHTML = `<div class="p-bar"><span class="p-title"></span><span class="p-timer">00:00</span></div><div class="p-next"></div><div class="p-notes"></div><div class="p-help">← → chuyển slide (cửa sổ chính đi theo) · R đặt lại đồng hồ</div>`;
    document.body.appendChild(pv);
    const style = document.createElement('style');
    style.textContent = `body.presenter-mode{overflow:auto;background:#0E181D}body.presenter-mode #stage,body.presenter-mode #help{display:none}#presenter{color:#EEF3F4;font-family:'Be Vietnam Pro',Arial,sans-serif;padding:28px 36px}.p-bar{display:flex;justify-content:space-between;font-size:22px;font-weight:700}.p-timer{font-variant-numeric:tabular-nums;color:#5AC8D8;font-size:40px}.p-next{color:#96A9B1;margin:8px 0 20px;font-size:18px}.p-notes{font-size:26px;line-height:1.6}.p-help{margin-top:28px;color:#6F8790;font-size:14px}`;
    document.head.appendChild(style);
    setInterval(() => { const s = Math.floor((Date.now() - t0) / 1000); pv.querySelector('.p-timer').textContent = `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`; }, 500);
    document.addEventListener('keydown', e => { if (e.key === 'r' || e.key === 'R') t0 = Date.now(); });
  }

  const start = parseInt(location.hash.slice(1), 10);
  slides[0].classList.add('active');
  fit();
  show(start ? start - 1 : 0, true);
})();
