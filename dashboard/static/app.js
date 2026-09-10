const state = { csrf: null, view: 'home', overview: null, detail: null };

const $ = (id) => document.getElementById(id);
const el = (tag, attrs = {}, children = []) => {
  const node = document.createElement(tag);
  Object.entries(attrs).forEach(([k, v]) => {
    if (k === 'class') node.className = v;
    else if (k === 'text') node.textContent = v;
    else if (k.startsWith('on')) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  });
  children.forEach((c) => node.append(c));
  return node;
};

async function api(path, opts = {}) {
  const headers = { ...(opts.headers || {}) };
  if (opts.body && !headers['Content-Type']) headers['Content-Type'] = 'application/json';
  if (opts.method && opts.method !== 'GET' && state.csrf) headers['X-CSRF-Token'] = state.csrf;
  const res = await fetch(path, { credentials: 'same-origin', ...opts, headers });
  if (res.status === 401) {
    showLogin();
    throw new Error('auth');
  }
  const data = await res.json().catch(() => ({ error: 'invalid response' }));
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}

function showLogin() {
  $('app').classList.add('hidden');
  $('login').classList.remove('hidden');
}

function showApp() {
  $('login').classList.add('hidden');
  $('app').classList.remove('hidden');
}

function money(block) {
  if (!block) return '$0';
  return `$${(block.usd ?? 0).toFixed(4)}`;
}

function pill(id, text, kind) {
  const node = $(id);
  node.textContent = text;
  node.className = 'pill' + (kind ? ` ${kind}` : '');
}

function renderHome(o) {
  const counts = o.task_counts || {};
  const budget = o.budget || {};
  const next = o.next_claimable;
  const main = $('main');
  main.replaceChildren(
    el('div', { class: 'banner', text: 'Assisted manual mode. The director console persists your instructions; it does not call a model or a broker.' }),
    el('div', { class: 'grid cards' }, [
      card('Integrity', [
        row('Frozen B3 plan', o.freeze?.ok ? 'verified' : 'mismatch'),
        row('Sources ingested', String(o.sources ?? 0)),
        row('Cycles', String((o.cycles || []).length)),
        row('Task claims used', `${o.attempts_used ?? 0} / ${o.policy?.max_tasks ?? '—'}`),
      ]),
      card('Queue', [
        row('Pending', String(counts.pending || 0)),
        row('Leased', String(counts.leased || 0)),
        row('Completed', String(counts.completed || 0)),
        row('Failed / blocked', `${counts.failed || 0} / ${counts.blocked || 0}`),
        row('Next claimable', next ? `${next.role} · ${next.task_id.slice(0, 18)}…` : 'none'),
      ]),
      card('Spend', [
        row('Period', budget.period_id || 'unset'),
        row('Limit', money(budget.limit)),
        row('Spent', money(budget.spent)),
        row('Reserved', money(budget.reserved)),
        row('Unknown costs', String(budget.unknown_count || 0)),
        row('Admission', budget.blocked ? 'blocked' : 'open'),
      ]),
      card('Director', [
        row('Owner', o.brief?.context_owner || 'internal_research_director'),
        row('Stopped', o.policy?.stopped ? 'yes' : 'no'),
        row('Families', String(o.families?.families?.length || 0)),
      ]),
    ]),
    el('div', { class: 'grid wide', style: 'margin-top:0.9rem' }, [
      controlPanel(),
      card('Latest director decisions', (o.brief?.latest_decisions || []).length
        ? [(o.brief.latest_decisions.map((d) => {
            const wrap = el('div', { class: 'row clickable', onclick: () => openTask(d.task_id) });
            wrap.append(el('span', { text: d.decision }), el('span', { class: 'muted mono', text: d.task_id.slice(0, 16) }));
            return wrap;
          }))]
        : [el('p', { class: 'muted', text: 'No director decisions yet.' })]),
    ]),
  );
}

function controlPanel() {
  const box = card('Control', []);
  const seed = el('button', { text: 'Seed CEF cycle', onclick: () => command('seed-cef') });
  const dispatch = el('button', { text: 'Dispatch next model call', onclick: () => command('dispatch', {}) });
  const stop = el('button', { class: 'ghost', text: 'Stop network', onclick: () => {
    const reason = prompt('Stop reason (required)');
    if (reason) command('stop', { reason });
  }});
  const resume = el('button', { class: 'ghost', text: 'Resume', onclick: () => command('resume') });
  box.append(el('div', { class: 'actions' }, [seed, dispatch, stop, resume]));
  const ingest = el('form');
  ingest.append(
    el('p', { class: 'muted', text: 'Ingest never downloads a URL. Paste original text and a stable source id.' }),
    field('Source id', 'source_id'),
    field('Published at (optional ISO)', 'published_at'),
    el('label', {}, [el('span', { text: 'Content' }), el('textarea', { name: 'content', maxlength: '16000' })]),
    el('div', { class: 'actions' }, [el('button', { type: 'submit', text: 'Ingest source' })]),
  );
  ingest.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ingest);
    await command('ingest', {
      source_id: fd.get('source_id'),
      published_at: fd.get('published_at') || null,
      content: fd.get('content'),
    });
  });
  box.append(ingest);
  return box;
}

function field(label, name) {
  return el('label', {}, [el('span', { text: label }), el('input', { name })]);
}

function card(title, rows) {
  const node = el('section', { class: 'card' }, [el('h2', { text: title })]);
  rows.flat().forEach((r) => node.append(r));
  return node;
}

function row(k, v) {
  return el('div', { class: 'row' }, [el('span', { class: 'muted', text: k }), el('span', { text: v })]);
}

async function command(name, payload = {}) {
  try {
    await api(`/api/control/${name}`, { method: 'POST', body: JSON.stringify(payload) });
    await loadOverview();
  } catch (err) {
    window.alert(err.message || String(err));
  }
}

function renderRoles(roles) {
  const main = $('main');
  const cards = (roles || []).map((r) => {
    const node = el('section', { class: 'card clickable', onclick: () => openRole(r.role) });
    node.append(
      el('h2', { text: r.role }),
      row('Open task', r.open_task ? r.open_task.state : 'idle'),
      row('Attempts', String(r.attempt_count)),
      row('Rejected submissions', String(r.error_count)),
      row('Prompt', r.active_prompt ? r.active_prompt.id.slice(0, 12) + '…' : 'none'),
      row('Model', r.route && r.route.model ? `${r.route.provider}:${r.route.model}` : 'unset'),
      row('Key', r.route && r.route.has_key ? `…${r.route.key_hint}` : 'missing'),
    );
    if (r.reviewer_blinded) node.append(el('p', { class: 'muted', text: 'Blinded to upstream interpretations.' }));
    return node;
  });
  main.replaceChildren(el('div', { class: 'grid cards' }, cards));
}

function renderRole(r) {
  const main = $('main');
  const tasks = el('table', {}, [
    el('thead', {}, [el('tr', {}, ['task', 'state', 'worker', 'hash'].map((h) => el('th', { text: h })))]),
  ]);
  const body = el('tbody');
  (r.tasks || []).forEach((t) => {
    const tr = el('tr', { class: 'clickable', onclick: () => openTask(t.task_id) });
    [t.task_id.slice(0, 18), t.state, t.worker_id || '—', (t.packet_hash || '').slice(0, 12)].forEach((c) => tr.append(el('td', { class: 'mono', text: c })));
    body.append(tr);
  });
  tasks.append(body);
  const memory = el('div');
  (r.memory_history || []).forEach((m) => {
    memory.append(el('div', { class: 'bubble' }, [
      el('div', { class: 'eyebrow', text: `v${m.version} · ${m.updated_at}` }),
      el('div', { text: m.memory || '' }),
    ]));
  });
  main.replaceChildren(
    el('p', { class: 'eyebrow clickable', text: '← Roles', onclick: () => setView('roles') }),
    el('h1', { text: r.role }),
    r.reviewer_blinded ? el('div', { class: 'banner', text: 'Reviewer is blinded. Packet drill-down is for your audit, not for feeding back into this role.' }) : '',
    el('div', { class: 'grid cards' }, [
      card('Load', [row('Attempts', String(r.attempt_count)), row('Errors', String(r.error_count)), row('Tasks', String(r.task_count))]),
      card('Active prompt', [el('div', { class: 'mono hash', text: r.active_prompt?.id || 'none' }), el('p', { class: 'muted', text: r.active_prompt?.rationale || '' })]),
    ]),
    card('Tasks', [tasks]),
    card('Working memory history', memory.childNodes.length ? [...memory.childNodes] : [el('p', { class: 'muted', text: 'No stored memory.' })]),
    card('Submission errors', [(r.submission_errors || []).length
      ? (r.submission_errors.map((e) => row(e.code, e.error_id)))
      : [el('p', { class: 'muted', text: 'None. Invalid results keep the lease and land here.' })]],
    ),
  );
}

function renderTask(t) {
  const main = $('main');
  main.replaceChildren(
    el('p', { class: 'eyebrow clickable', text: '← Back', onclick: () => history.back() }),
    el('h1', { text: t.role }),
    t.blinding ? el('div', { class: 'banner', text: t.blinding }) : '',
    card('Identity', [
      row('Task', t.task_id),
      row('State', t.state),
      row('Worker', t.worker_id || '—'),
      row('Packet hash', t.packet_hash || '—'),
      row('Result hash', t.result_hash || '—'),
    ]),
    card('Frozen packet', [el('pre', { class: 'mono', text: JSON.stringify(t.packet, null, 2) })]),
    card('Result', [el('pre', { class: 'mono', text: t.result ? JSON.stringify(t.result, null, 2) : 'not submitted' })]),
    card('Attempts', [(t.attempts || []).map((a) => row(a.outcome || 'open', a.attempt_id))]),
  );
}

// Self-contained: writes provider secrets straight into the gitignored .env.
// The server allowlists the variable names, so nothing here can touch the
// login password or the budget.
function envCard(env) {
  const box = card('Provider keys · .env', []);
  box.append(el('p', { class: 'muted', text: env.note }));
  (env.writable || []).filter((k) => k.secret).forEach((k) => {
    const name = k.key.replace('_API_KEY', '').toLowerCase();
    box.append(row(name, k.set ? `key …${k.hint}` : 'not set'));
  });

  const form = el('form');
  const provider = el('select', { name: 'provider' });
  Object.keys(env.providers || {}).forEach((p) => provider.append(el('option', { value: p, text: p })));
  const key = el('input', {
    name: 'key', type: 'password', autocomplete: 'off', spellcheck: 'false',
    placeholder: 'paste the key — blank keeps the current one',
  });
  const model = el('input', { name: 'model', placeholder: 'default model id (optional)' });
  const base = el('input', { name: 'base', placeholder: 'base URL (optional)' });
  const note = el('p', { class: 'muted' });
  form.append(
    el('label', {}, [el('span', { text: 'Provider' }), provider]),
    el('label', {}, [el('span', { text: 'API key' }), key]),
    el('label', {}, [el('span', { text: 'Default model' }), model]),
    el('label', {}, [el('span', { text: 'Base URL' }), base]),
    el('div', { class: 'actions' }, [el('button', { type: 'submit', text: 'Save to .env' })]),
    note,
  );
  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const names = env.providers[provider.value];
    const values = {};
    if (key.value.trim()) values[names.key] = key.value.trim();
    if (model.value.trim()) values[names.model] = model.value.trim();
    if (base.value.trim()) values[names.base] = base.value.trim();
    if (!Object.keys(values).length) {
      note.textContent = 'Nothing to save.';
      return;
    }
    try {
      await api('/api/env', { method: 'POST', body: JSON.stringify({ values }) });
      key.value = '';
      setView('spend');
    } catch (err) {
      note.textContent = err.message || String(err);
    }
  });
  box.append(form);

  const routes = el('form');
  const inputs = {};
  routes.append(el('p', { class: 'muted', text: 'Role routing is provider:model. Blank unmaps the role.' }));
  (env.routes || []).forEach((r) => {
    const value = r.configured ? `${r.provider}:${r.model}` : '';
    inputs[env.roles[r.role]] = el('input', { name: r.role, value, placeholder: 'openai:gpt-5.4' });
    routes.append(el('label', {}, [el('span', { text: r.role }), inputs[env.roles[r.role]]]));
  });
  const routeNote = el('p', { class: 'muted' });
  routes.append(el('div', { class: 'actions' }, [el('button', { type: 'submit', text: 'Save routing' })]), routeNote);
  routes.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const values = {};
    Object.entries(inputs).forEach(([name, input]) => { values[name] = input.value.trim(); });
    try {
      await api('/api/env', { method: 'POST', body: JSON.stringify({ values }) });
      setView('spend');
    } catch (err) {
      routeNote.textContent = err.message || String(err);
    }
  });
  box.append(routes);

  if (!env.budget_configured) {
    box.append(el('p', { class: 'muted', text: 'A key alone does not enable dispatch. Set RESEARCH_BUDGET_PERIOD and RESEARCH_BUDGET_LIMIT_USD in .env yourself, then restart, because the console cannot open or raise a spending period.' }));
  }
  return box;
}

function renderSpend(data, env) {
  const b = data.ledger || {};
  const main = $('main');
  const form = el('form');
  form.append(
    el('p', { class: 'muted', text: 'Keys live in gitignored .env. This page shows aliases and last-four only. Dispatch sends one packet.' }),
    field('Alias', 'alias'),
    field('Provider', 'provider'),
    field('Model (optional)', 'model'),
    field('Key hint last4 (optional)', 'key_hint'),
    el('div', { class: 'actions' }, [el('button', { type: 'submit', text: 'Save alias' })]),
  );
  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const fd = new FormData(form);
    await api('/api/accounts', { method: 'POST', body: JSON.stringify(Object.fromEntries(fd)) });
    setView('spend');
  });
  const attempts = el('table', {}, [
    el('thead', {}, [el('tr', {}, ['attempt', 'state', 'max', 'actual', 'provider req'].map((h) => el('th', { text: h })))]),
  ]);
  const tb = el('tbody');
  (b.attempts || []).forEach((a) => {
    const tr = el('tr');
    [a.attempt_id, a.state, String(a.maximum_microusd), String(a.actual_microusd ?? '—'), a.provider_request_id || '—'].forEach((c) => tr.append(el('td', { class: 'mono', text: c })));
    tb.append(tr);
  });
  attempts.append(tb);
  main.replaceChildren(
    el('div', { class: 'banner', text: b.note || '' }),
    el('div', { class: 'grid cards' }, [
      card('Ledger', [
        row('Period', b.period_id || '—'),
        row('Limit', money(b.limit)),
        row('Spent', money(b.spent)),
        row('Reserved', money(b.reserved)),
        row('Available', money(b.available)),
        row('Unknown', String(b.unknown_count || 0)),
        row('Stopped', b.stopped ? (b.stop_reason || 'yes') : 'no'),
        row('Blocked', b.blocked ? 'yes' : 'no'),
      ]),
    ]),
    card('Attempts (fail-closed)', [attempts]),
    card('Env role routing', [
      ...(data.routes || []).map((a) => row(
        a.role,
        a.configured ? `${a.provider}:${a.model} · ${a.has_key ? 'key …' + a.key_hint : 'no key'}` : 'unmapped',
      )),
      el('div', { class: 'actions' }, [el('button', { text: 'Dispatch next model call', onclick: () => command('dispatch', {}) })]),
    ]),
    envCard(env),
    card('Optional UI aliases', [
      ...(data.accounts || []).map((a) => row(`${a.alias} · ${a.provider}`, a.model || a.key_hint || '')),
      form,
    ]),
  );
}

function renderFamilies(data) {
  const main = $('main');
  const families = (data.families || []).map((f) => card(f.candidate_id, [
    row('Family', f.family_id),
    row('Status', f.status),
    el('p', { text: f.mechanism_summary }),
    el('div', { class: 'mono hash', text: f.frozen_plan_hash || '' }),
  ]));
  const form = el('form');
  form.append(
    field('Family id', 'family_id'),
    field('Cycle id (optional)', 'cycle_id'),
    el('label', {}, [el('span', { text: 'Bottleneck' }), el('textarea', { name: 'bottleneck' })]),
    el('div', { class: 'actions' }, [el('button', { type: 'submit', text: 'Record retrospective' })]),
  );
  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const fd = new FormData(form);
    await api('/api/families/retrospective', { method: 'POST', body: JSON.stringify({
      family_id: fd.get('family_id'), cycle_id: fd.get('cycle_id') || null, bottleneck: fd.get('bottleneck'),
    })});
    setView('families');
  });
  main.replaceChildren(
    el('p', { class: 'muted', text: 'Minimal registry: IDs, mechanism text, frozen-plan hash, reviewed links. No similarity engine.' }),
    el('div', { class: 'grid cards' }, families.length ? families : [el('p', { class: 'muted', text: 'No families yet. Seed the CEF cycle from Mission.' })]),
    card('Linked cycles', [(data.cycle_links || []).map((l) => row(l.cycle_id, l.family_id))]),
    card('Retrospectives', [
      ...(data.retrospectives || []).map((r) => el('p', { text: r.bottleneck })),
      form,
    ]),
  );
}

function briefSummary(brief) {
  const next = (brief?.pending_and_leased || [])[0];
  return [
    row('Owner', brief?.context_owner || '—'),
    row('Objective', (brief?.objective || '').slice(0, 180)),
    row('Pending / leased', String(brief?.counts?.pending_and_leased_total ?? 0)),
    row('Next task', next ? `${next.role} · ${next.state}` : 'none'),
    row('Stopped', brief?.policy?.stopped ? 'yes' : 'no'),
  ];
}

function renderOrchestrator(data, brief) {
  const main = $('main');
  const transcript = el('div', { class: 'transcript' });
  (data.messages || []).forEach((m) => {
    transcript.append(el('div', { class: `bubble ${m.author}` }, [
      el('div', { class: 'eyebrow', text: `${m.author} · ${m.created_at}` }),
      el('div', { text: m.body }),
    ]));
  });
  if (!(data.messages || []).length) {
    transcript.append(el('p', { class: 'muted', text: 'No messages yet. Send an instruction or /help.' }));
  }
  const composer = el('form', { class: 'composer' });
  const box = el('textarea', {
    id: 'director-input',
    placeholder: 'Talk to the internal director. Free text is persisted. /help for commands.',
    maxlength: '8000',
  });
  composer.append(box, el('button', { id: 'director-send', type: 'submit', text: 'Send' }));
  composer.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    if (!box.value.trim()) return;
    await api('/api/messages', { method: 'POST', body: JSON.stringify({ body: box.value })});
    box.value = '';
    setView('orchestrator');
  });
  const ideas = el('form');
  const ideaBox = el('textarea', { id: 'idea-input', placeholder: 'Capture an idea without running a cycle.', maxlength: '4000' });
  ideas.append(ideaBox, el('div', { class: 'actions' }, [el('button', { id: 'idea-save', type: 'submit', text: 'Save idea' })]));
  ideas.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    if (!ideaBox.value.trim()) return;
    await api('/api/ideas', { method: 'POST', body: JSON.stringify({ body: ideaBox.value })});
    ideaBox.value = '';
    setView('orchestrator');
  });
  main.replaceChildren(
    el('section', { class: 'card' }, [
      el('h2', { text: 'Director console' }),
      el('p', { class: 'muted', text: 'Persistent. The director owns planning and prompt proposals, not the controller or the budget. No model is started until you approve spend.' }),
      composer,
      transcript,
    ]),
    el('div', { class: 'grid wide', style: 'margin-top:0.9rem' }, [
      card('Live brief', briefSummary(brief)),
      card('Standing jobs', [(data.jobs || []).length
        ? (data.jobs || []).map((j) => row(j.kind, `${j.status} · ${j.job_id.slice(0, 10)}`))
        : [el('p', { class: 'muted', text: 'None yet.' })]],
      ),
      card('Idea inbox', [
        ...(data.ideas || []).map((i) => el('p', { text: i.body })),
        ideas,
      ]),
    ]),
  );
  transcript.scrollTop = transcript.scrollHeight;
}

function renderAudit(data) {
  const main = $('main');
  main.replaceChildren(
    card('Operator audit log', [(data.audit || []).map((a) => row(`${a.created_at} · ${a.action}`, a.detail || a.actor))]),
    card('Ingested sources (metadata)', [(data.sources || []).map((s) => row(s.source_id, `${s.chars} chars · ${s.event_id.slice(0, 14)}`))]),
  );
}

function openRole(name) { location.hash = `role/${name}`; }
function openTask(id) { location.hash = `task/${id}`; }

async function setView(name, extra) {
  state.view = name;
  document.querySelectorAll('nav button').forEach((b) => b.classList.toggle('active', b.dataset.view === name));
  if (name === 'home') {
    const o = await api('/api/overview');
    state.overview = o;
    pill('mode-pill', o.mode.replace('_', ' '), 'good');
    pill('spend-pill', o.budget.blocked ? `blocked · ${money(o.budget.spent)}` : money(o.budget.spent), o.budget.blocked ? 'warn' : 'good');
    renderHome(o);
  } else if (name === 'roles') {
    renderRoles((await api('/api/roles')).roles);
  } else if (name === 'role') {
    renderRole(await api(`/api/roles/${extra}`));
  } else if (name === 'task') {
    renderTask(await api(`/api/tasks/${extra}`));
  } else if (name === 'spend') {
    const [spend, env] = await Promise.all([api('/api/spend'), api('/api/env')]);
    renderSpend(spend, env);
  } else if (name === 'families') {
    renderFamilies(await api('/api/families'));
  } else if (name === 'orchestrator') {
    const [messages, brief] = await Promise.all([api('/api/messages'), api('/api/brief')]);
    renderOrchestrator(messages, brief);
  } else if (name === 'audit') {
    renderAudit(await api('/api/audit'));
  }
}

function route() {
  const hash = location.hash.replace('#', '');
  if (hash.startsWith('role/')) return setView('role', hash.slice(5));
  if (hash.startsWith('task/')) return setView('task', hash.slice(5));
  const view = hash || 'home';
  return setView(['home', 'roles', 'families', 'spend', 'orchestrator', 'audit'].includes(view) ? view : 'home');
}

async function loadOverview() { return setView(state.view === 'role' || state.view === 'task' ? 'home' : state.view); }

$('login-form').addEventListener('submit', async (ev) => {
  ev.preventDefault();
  $('login-error').textContent = '';
  try {
    const data = await api('/api/login', { method: 'POST', body: JSON.stringify({ password: $('password').value }) });
    state.csrf = data.csrf;
    showApp();
    route();
  } catch (err) {
    $('login-error').textContent = err.message === 'auth' ? 'Invalid password' : err.message;
  }
});

$('logout').addEventListener('click', async () => {
  await api('/api/logout', { method: 'POST', body: '{}' });
  state.csrf = null;
  showLogin();
});

document.querySelectorAll('nav button').forEach((b) => b.addEventListener('click', () => {
  location.hash = b.dataset.view === 'home' ? '' : b.dataset.view;
}));

window.addEventListener('hashchange', route);

(async function boot() {
  try {
    const me = await api('/api/me');
    state.csrf = me.csrf;
    showApp();
    route();
  } catch (err) {
    showLogin();
  }
})();
