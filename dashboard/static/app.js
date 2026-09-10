'use strict';

/* Opportunity Engine operator console.
 *
 * Six tabs over the real local records. Every write goes to an existing
 * controller endpoint; nothing here fabricates state. The console cannot open
 * or raise a spending period, so no control on screen offers to.
 */

const NAV = [
  ['director', 'Director'],
  ['status', 'Status'],
  ['pipeline', 'Pipeline'],
  ['ideas', 'Ideas'],
  ['budget', 'Budget'],
  ['history', 'History'],
];
const VIEWS = NAV.map(([key]) => key);

const C = {
  amber: '#e0a94a',
  green: '#4fbd8b',
  slate: '#8a94a3',
  red: '#c96a5a',
  dim: '#948c7e',
  ink: '#f2ede4',
};

const STEPS = [
  { id: 'director_plan', num: '01', title: 'Plan the cycle',
    desc: 'Turns the frozen plan into a list of tasks nobody has claimed yet.' },
  { id: 'researcher', num: '02', title: 'Gather evidence',
    desc: 'Reads the documents you added and drafts findings from them.' },
  { id: 'data_auditor', num: '03', title: 'Check the data',
    desc: 'Rejects any claim that cannot be traced back to a source.' },
  { id: 'reviewer', num: '04', title: 'Review, blinded', blinded: true,
    desc: 'Judges the packet on its own merits, without seeing upstream reasoning.' },
  { id: 'director_decision', num: '05', title: 'Decide',
    desc: 'Accepts the packet, rejects it, or sends the cycle back a step.' },
  { id: 'improvement_proposal', num: '06', title: 'Propose improvements',
    desc: 'Writes prompt changes for the next cycle. Nothing applies automatically.' },
];

const BUCKETS = [
  { keys: ['pending'], label: 'Waiting to be claimed', color: C.amber, gloss: 'ready for a step to pick up' },
  { keys: ['leased'], label: 'Being worked on', color: C.green, gloss: 'leased right now' },
  { keys: ['completed'], label: 'Finished', color: C.slate, gloss: 'decided by the director' },
  { keys: ['failed', 'blocked'], label: 'Failed or blocked', color: C.red, gloss: 'kept — a rejection is a result' },
];

const DECISION_COLOR = {
  continue: C.green, propose_improvement: C.green,
  reject: C.amber, review_required: C.amber,
  blocked: C.red, inconclusive: C.slate,
};

const FILTERS = ['All', 'Access', 'Documents', 'Cycles', 'Ideas', 'Keys', 'Messages'];

// Audit details are opaque ids or small JSON blobs. Turn them into sentences.
function detailJson(detail) {
  try { return JSON.parse(detail); } catch (err) { return null; }
}

const AUDIT = {
  login: ['Access', () => 'Signed in.'],
  login_failed: ['Access', (d) => `Failed sign-in attempt${d ? ' from ' + d : ''}.`],
  logout: ['Access', () => 'Signed out.'],
  ingest: ['Documents', () => 'Added a document.'],
  seed_cef: ['Cycles', () => 'Seeded a CEF cycle.'],
  stop: ['Cycles', (d) => `Stopped new task claims${d ? ': ' + d : '.'}`],
  resume: ['Cycles', () => 'Resumed task claims.'],
  claim: ['Cycles', (d) => {
    const value = detailJson(d) || {};
    return `Leased a task to ${value.worker || 'a worker'}${value.role ? ` for ${value.role}` : ''}.`;
  }],
  submit: ['Cycles', (d) => `Submitted a result for ${short(d, 18)}.`],
  fail: ['Cycles', (d) => `Marked ${short(d, 18)} failed.`],
  dispatch: ['Cycles', (d) => {
    const value = detailJson(d) || {};
    return `Sent one ${value.role || ''} packet to ${value.model || 'a model'}.`.replace('  ', ' ');
  }],
  idea: ['Ideas', () => 'Parked an idea.'],
  retrospective: ['Ideas', () => 'Recorded a retrospective.'],
  env_update: ['Keys', (d) => {
    const items = detailJson(d);
    if (!Array.isArray(items)) return 'Updated provider settings in .env.';
    const set = items.filter((item) => item.set).map((item) => item.key);
    const cleared = items.filter((item) => !item.set).map((item) => item.key);
    const parts = [];
    if (set.length) parts.push(`set ${set.join(', ')}`);
    if (cleared.length) parts.push(`cleared ${cleared.join(', ')}`);
    return `Edited .env — ${parts.join('; ') || 'no change'}.`;
  }],
  account_upsert: ['Keys', (d) => `Saved the provider alias ${d}.`],
  orchestrator_message: ['Messages', () => 'Sent an instruction to the director.'],
  command: ['Messages', (d) => `Ran ${d} from the director console.`],
};

const state = {
  csrf: null,
  operator: 'james',
  tab: 'director',
  extra: null,
  overview: null,
  draft: '',
  role: null,
  openTask: null,
  filter: 'All',
  showIngest: false,
  showStop: false,
  showHost: false,
  focusVendor: null,
  flash: '',
};

/* ---------- dom helpers ---------- */

const $ = (id) => document.getElementById(id);

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  Object.entries(attrs).forEach(([key, value]) => {
    if (value === null || value === undefined || value === false) return;
    if (key === 'class') node.className = value;
    else if (key === 'text') node.textContent = value;
    else if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value);
  });
  (Array.isArray(children) ? children : [children])
    .flat(Infinity)
    .filter((child) => child !== null && child !== undefined && child !== false && child !== '')
    .forEach((child) => node.append(child));
  return node;
}

const txt = (value) => document.createTextNode(value);
const card = (children, cls) => el('section', { class: cls ? `card ${cls}` : 'card' }, children);
const rows = (children) => el('div', { class: 'rows' }, children);
const dot = (color, cls = 'dot-lg') => el('span', { class: cls, style: `background:${color}` });
const btn = (label, onclick, cls) => el('button', { class: cls ? `btn ${cls}` : 'btn', type: 'button', text: label, onclick });

function eyebrow(label, right) {
  const head = el('div', { class: 'eyebrow', text: label });
  if (!right) return head;
  return el('div', { class: 'eyebrow-row' }, [head, el('span', { class: 'note', text: right })]);
}

function drow(key, value, color) {
  return el('div', { class: 'drow' }, [
    el('span', { class: 'k', text: key }),
    el('span', { class: 'v', text: value, style: color ? `color:${color}` : null }),
  ]);
}

function empty(lines, cls) {
  return el('div', { class: cls ? `empty ${cls}` : 'empty' }, lines.map((line) => el('div', { text: line })));
}

function field(label, input, help, optional) {
  return el('label', { class: 'field' }, [
    el('span', { class: 'lbl' }, [txt(label), optional ? el('span', { class: 'opt', text: ' — optional' }) : null]),
    input,
    help ? el('span', { class: 'help', text: help }) : null,
  ]);
}

function pageHead(title, sub, sub2) {
  return el('div', { class: 'page-head' }, [
    el('h1', { text: title }),
    sub ? el('p', { class: 'sub', text: sub }) : null,
    sub2 ? el('p', { class: 'sub-2', text: sub2 }) : null,
  ]);
}

function page(children) {
  const y = state.restoreScroll;
  state.restoreScroll = null;
  $('main').replaceChildren(el('div', { class: 'page' }, children));
  if (typeof y === 'number') requestAnimationFrame(() => window.scrollTo(0, y));
  else window.scrollTo(0, 0);
}

/* ---------- formatting ---------- */

function money(block) {
  const usd = (block && block.usd) || 0;
  if (usd === 0) return '$0.00';
  if (usd < 0.01) return `$${usd.toFixed(4)}`;
  return `$${usd.toFixed(2)}`;
}

function stamp(iso) {
  if (!iso) return '—';
  const when = new Date(iso);
  if (Number.isNaN(when.getTime())) return String(iso).slice(0, 16);
  const pad = (n) => String(n).padStart(2, '0');
  return `${pad(when.getMonth() + 1)}-${pad(when.getDate())} ${pad(when.getHours())}:${pad(when.getMinutes())}`;
}

const day = (iso) => (iso ? String(iso).slice(0, 10) : '—');
const short = (value, n = 12) => (value ? String(value).slice(0, n) : '—');
const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;

/* ---------- transport ---------- */

async function api(path, opts = {}) {
  const headers = { ...(opts.headers || {}) };
  if (opts.body && !headers['Content-Type']) headers['Content-Type'] = 'application/json';
  if (opts.method && opts.method !== 'GET' && state.csrf) headers['X-CSRF-Token'] = state.csrf;
  const res = await fetch(path, { credentials: 'same-origin', ...opts, headers });
  if (res.status === 401) {
    showLogin();
    throw new Error('Your session expired. Sign in again.');
  }
  const data = await res.json().catch(() => ({ error: 'invalid response' }));
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}

const post = (path, payload) => api(path, { method: 'POST', body: JSON.stringify(payload || {}) });

function reportInto(node) {
  return (err) => { node.textContent = err && err.message ? err.message : String(err); };
}

/* ---------- rail ---------- */

function renderRail() {
  const overview = state.overview || {};
  const budget = overview.budget || {};
  const stopped = !!(overview.policy && overview.policy.stopped);

  $('nav').replaceChildren(...NAV.map(([key, label]) => el('button', {
    type: 'button',
    class: state.tab === key ? 'active' : '',
    onclick: () => go(key),
  }, [el('span', { class: 'dot' }), txt(label)])));

  $('rail-state').replaceChildren(
    el('div', { class: 'rail-row' }, [
      el('span', { class: 'k', text: 'Task claims' }),
      el('span', {
        class: 'v', text: stopped ? 'stopped' : 'admitted',
        style: `color:${stopped ? C.amber : C.green}`,
      }),
    ]),
    el('div', { class: 'rail-row' }, [
      el('span', { class: 'k', text: 'Spending' }),
      el('span', {
        class: 'v',
        text: budget.blocked ? `blocked · ${money(budget.spent)}` : `${money(budget.spent)} of ${money(budget.limit)}`,
        style: `color:${budget.blocked ? C.amber : C.green}`,
      }),
    ]),
  );
  $('operator').textContent = state.operator;
}

function spendPhrase(budget) {
  return budget.blocked
    ? `blocked at ${money(budget.spent)}`
    : `open, ${money(budget.spent)} of ${money(budget.limit)} used`;
}

/* ---------- director ---------- */

function renderDirector(inbox) {
  const overview = state.overview;
  const brief = overview.brief || {};
  const counts = overview.task_counts || {};
  const budget = overview.budget || {};
  const pending = counts.pending || 0;
  const leased = counts.leased || 0;
  const next = overview.next_claimable;
  const hour = new Date().getHours();
  const partOfDay = hour < 12 ? 'morning' : hour < 18 ? 'afternoon' : 'evening';
  const headline = (pending || leased)
    ? `${leased === 1 ? '1 task is' : leased + ' tasks are'} in flight and ${pending === 1 ? '1 task is' : pending + ' tasks are'} waiting. Spending is ${spendPhrase(budget)}.`
    : `Nothing is running yet. Spending is ${spendPhrase(budget)}, so no step can cost you anything.`;

  const problem = el('p', { class: 'muted' });
  const box = el('textarea', {
    placeholder: 'Tell the director what to work on. Plain English, or a / command.',
    maxlength: '8000',
  });
  box.value = state.draft;
  box.addEventListener('input', () => { state.draft = box.value; });
  box.addEventListener('keydown', (ev) => {
    if (ev.key === 'Enter' && (ev.metaKey || ev.ctrlKey)) { ev.preventDefault(); send(); }
  });

  async function send() {
    const body = box.value.trim();
    if (!body) return;
    problem.textContent = '';
    try {
      await post('/api/messages', { body });
      state.draft = '';
      await refresh();
    } catch (err) { reportInto(problem)(err); }
  }

  const commands = ['/brief', '/status', '/seed-cef', '/stop ', '/resume', '/idea ', '/help'];
  if (overview.provider_dispatch) commands.splice(3, 0, '/dispatch ');
  const chips = el('div', { class: 'chips' }, commands.map((cmd) => el('button', {
    class: 'chip', type: 'button', text: cmd.trim(),
    onclick: () => { box.value = cmd; state.draft = cmd; box.focus(); },
  })));

  const composer = card([
    box,
    chips,
    el('div', { class: 'foot' }, [
      el('p', { class: 'hint', text: 'Saved for the director. Free text starts nothing; slash commands act on the controller.' }),
      btn('Send', send),
    ]),
    problem,
  ], 'tight composer');

  const messages = (inbox.messages || []).slice().reverse();
  const transcript = messages.length
    ? el('div', { class: 'msgs' }, messages.map((message) => {
      const mine = message.author === 'james';
      return el('div', { class: mine ? 'msg mine' : 'msg' }, [
        el('div', { class: 'head' }, [
          el('span', { class: 'who', text: mine ? state.operator : message.author === 'director' ? 'Director' : 'System' }),
          el('span', { class: 'tag', text: mine ? 'instruction' : 'recorded locally' }),
          el('span', { class: 'time', text: stamp(message.created_at) }),
        ]),
        el('div', { class: 'body', text: message.body }),
      ]);
    }))
    : empty(['Nothing said yet.', 'Try /brief to see what the director is holding.']);

  const ideaBox = el('textarea', {
    placeholder: 'Write it down now, decide later. Nothing starts.',
    maxlength: '4000', style: 'min-height:70px;font-size:13px',
  });
  const ideaProblem = el('p', { class: 'muted' });
  const ideaCount = (inbox.ideas || []).length;

  const doNext = card([
    eyebrow('Do next'),
    el('button', { class: 'option', type: 'button', onclick: () => go('status') }, [
      el('span', { class: 't', text: 'Seed a research cycle' }),
      el('span', { class: 'd', text: 'Registers the CEF feasibility idea and fills the queue.' }),
    ]),
    el('button', {
      class: 'option', type: 'button',
      onclick: () => { state.showIngest = true; go('status'); },
    }, [
      el('span', { class: 't', text: 'Add a document' }),
      el('span', { class: 'd', text: 'Paste the text yourself. Links are never fetched.' }),
    ]),
    el('div', { class: 'rail-hint' }, [
      txt(overview.provider_dispatch
        ? 'A spending period is open, so /dispatch can send one packet at a time. '
        : 'Paid steps stay blocked until an allowance is set through the controller. This console cannot raise it. '),
      el('button', { class: 'btn link', type: 'button', text: 'See the ledger', onclick: () => go('budget') }),
    ]),
  ], 'tight');

  const liveBrief = card([
    eyebrow('Live brief', 'bounded context'),
    el('p', { class: 'objective', text: brief.objective || '—' }),
    rows([
      drow('Owner', brief.context_owner || 'internal_research_director'),
      drow('Waiting / working', `${pending} / ${leased}`),
      drow('Next task', next ? short(next.task_id, 18) : 'none'),
    ]),
  ], 'tight');

  const parkIdea = card([
    eyebrow('Park an idea'),
    ideaBox,
    el('div', {}, [btn('Save to inbox', async () => {
      const body = ideaBox.value.trim();
      if (!body) return;
      ideaProblem.textContent = '';
      try {
        await post('/api/ideas', { body });
        await refresh();
      } catch (err) { reportInto(ideaProblem)(err); }
    }, 'secondary small')]),
    ideaCount ? el('div', { class: 'note', text: `${ideaCount} in inbox` }) : null,
    ideaProblem,
  ], 'tight');

  page([
    el('div', { class: 'page-head' }, [
      el('h1', { text: `Good ${partOfDay}, ${state.operator}.` }),
      el('p', { class: 'sub', text: headline }),
      el('p', { class: 'sub-2', text: 'A research controller. It discovers, rejects, and refines opportunities under frozen rules. It places no orders, and a rejection is a result.' }),
    ]),
    el('div', { class: 'split' }, [
      el('div', { class: 'col' }, [composer, transcript]),
      el('div', { class: 'col' }, [doNext, liveBrief, parkIdea]),
    ]),
  ]);
}

/* ---------- status ---------- */

function renderStatus() {
  const overview = state.overview;
  const counts = overview.task_counts || {};
  const budget = overview.budget || {};
  const freeze = overview.freeze || {};
  const policy = overview.policy || {};
  const next = overview.next_claimable;
  const sources = overview.sources || 0;
  const cycles = (overview.cycles || []).length;
  const used = overview.attempts_used || 0;
  const cap = policy.max_tasks || 0;
  const stopped = !!policy.stopped;

  const buckets = BUCKETS.map((bucket) => ({
    ...bucket,
    count: bucket.keys.reduce((total, key) => total + (counts[key] || 0), 0),
  }));
  const total = buckets.reduce((sum, bucket) => sum + bucket.count, 0);

  const planLine = freeze.ok
    ? 'The frozen plan checks out. '
    : 'The frozen plan does not match its receipt, so seeding is refused. ';
  const activity = (sources || cycles || total)
    ? `${plural(sources, 'document')} in, ${plural(cycles, 'cycle')} run, ${plural(counts.pending || 0, 'task')} waiting.`
    : 'Nothing has been added or run yet.';

  const metrics = el('div', { class: 'metrics' }, [
    el('div', { class: 'metric' }, [
      el('div', { class: 'k', text: 'Plan integrity' }),
      el('div', { class: 'v' }, [dot(freeze.ok ? C.green : C.red), txt(freeze.ok ? 'Verified' : 'Mismatch')]),
      el('div', { class: 'cap', text: `frozen B3 plan · ${short(freeze.sha256)}` }),
    ]),
    el('div', { class: 'metric' }, [
      el('div', { class: 'k', text: 'Documents in' }),
      el('div', { class: 'v', text: String(sources) }),
      el('div', { class: 'cap', text: `${plural(cycles, 'cycle')} run` }),
    ]),
    el('div', { class: 'metric' }, [
      el('div', { class: 'k', text: 'Task claims used' }),
      el('div', { class: 'v', text: `${used} of ${cap || '—'}` }),
      el('div', { class: 'bar' }, [el('i', { style: `width:${cap ? Math.min(100, Math.round((used / cap) * 100)) : 0}%` })]),
    ]),
    budget.blocked
      ? el('div', { class: 'metric warn' }, [
        el('div', { class: 'k', text: 'Spending' }),
        el('div', { class: 'v', text: 'Blocked' }),
        el('div', { class: 'cap', text: blockedReason(budget) }),
      ])
      : el('div', { class: 'metric' }, [
        el('div', { class: 'k', text: 'Spending' }),
        el('div', { class: 'v', text: money(budget.spent) }),
        el('div', { class: 'cap', text: `of ${money(budget.limit)} · period ${budget.period_id || 'none'}` }),
      ]),
  ]);

  const queue = card([
    eyebrow('Work queue', `next claimable · ${next ? short(next.task_id, 16) : 'none'}`),
    el('div', { class: 'meter' }, buckets.filter((b) => b.count > 0).map((bucket) => el('i', {
      style: `background:${bucket.color};width:${Math.round((bucket.count / total) * 100)}%`,
    }))),
    rows(buckets.map((bucket) => el('div', { class: 'qrow' }, [
      el('span', { class: 'swatch', style: `background:${bucket.color}` }),
      el('span', { class: 'lbl', text: bucket.label }),
      el('span', { class: 'gloss', text: bucket.gloss }),
      el('span', { class: 'n', text: String(bucket.count) }),
    ]))),
  ]);

  const decisions = (overview.brief && overview.brief.latest_decisions) || [];
  const decisionCard = card([
    eyebrow('Recent decisions'),
    decisions.length
      ? rows(decisions.map((decision) => el('button', {
        class: 'tl', type: 'button', onclick: () => { location.hash = `task/${decision.task_id}`; },
      }, [
        dot(DECISION_COLOR[decision.decision] || C.dim),
        el('span', { class: 'stack' }, [
          el('span', { class: 'txt', text: decision.summary || decision.decision }),
          el('span', { class: 'meta', text: `${decision.role} · ${decision.decision}` }),
        ]),
      ])))
      : empty(['No decisions yet.', 'They appear here after a cycle reaches review.']),
  ]);

  const controls = card([
    eyebrow('Controls'),
    el('div', { class: 'actions' }, [
      btn('Seed a research cycle', seedCycle),
      btn(stopped ? 'Already stopped' : 'Stop new claims', () => {
        if (stopped) { flash('New claims are already stopped.'); return; }
        state.showStop = !state.showStop;
        refresh();
      }, 'secondary danger'),
      btn('Resume claims', resumeClaims, 'secondary ok'),
      el('span', { class: 'spacer', text: 'Stopping only holds back new task claims. Open leases, memories, and the ledger are left alone.' }),
    ]),
    state.showStop && !stopped ? stopForm() : null,
    state.flash ? el('div', { class: 'flash', text: state.flash }) : null,
  ]);

  page([
    pageHead('Status', planLine + activity),
    metrics,
    el('div', { class: 'two-up' }, [queue, decisionCard]),
    controls,
    ingestCard(),
  ]);
}

function blockedReason(budget) {
  if (!budget.period_id) return 'No period is open, so no paid step can run.';
  if (budget.stopped) return `The ledger is stopped: ${budget.stop_reason || 'no reason recorded'}.`;
  if (budget.unknown_count) return `${plural(budget.unknown_count, 'attempt')} with an unknown cost must be reconciled first.`;
  if (budget.over_budget) return 'Spent plus reserved exceeds the allowance.';
  return 'New admissions are refused.';
}

function stopForm() {
  const reason = el('input', { placeholder: 'Why are you holding claims back?', maxlength: '2000' });
  const problem = el('p', { class: 'muted' });
  const form = el('div', { class: 'disclosure' }, [
    field('Stop reason', reason, 'Recorded with the stop. Required.'),
    el('div', { class: 'actions' }, [
      btn('Stop new claims', async () => {
        if (!reason.value.trim()) { problem.textContent = 'A reason is required.'; return; }
        try {
          await post('/api/control/stop', { reason: reason.value.trim() });
          state.showStop = false;
          flash('New task claims stopped. Open leases, memories, and the ledger are untouched.');
          await refresh();
        } catch (err) { reportInto(problem)(err); }
      }, 'secondary danger'),
      btn('Cancel', () => { state.showStop = false; refresh(); }, 'secondary'),
    ]),
    problem,
  ]);
  return form;
}

async function seedCycle() {
  try {
    const result = await post('/api/control/seed-cef', {});
    flash(result.duplicate
      ? 'A cycle is already registered against the frozen B3 plan. Seeding again is refused.'
      : 'Seeded. B3-H1-v1 registered and the queue filled. No model was called.');
  } catch (err) {
    flash(err.message || String(err));
  }
  await refresh();
}

async function resumeClaims() {
  const policy = (state.overview && state.overview.policy) || {};
  if (!policy.stopped) { flash('Claims are already being admitted.'); return; }
  try {
    await post('/api/control/resume', {});
    flash('Task claims admitted again. Existing leases were never dropped.');
  } catch (err) {
    flash(err.message || String(err));
  }
  await refresh();
}

function isoDate(value) {
  const text = (value || '').trim();
  if (!text) return null;
  // The controller requires a timezone; a bare date is read as UTC midnight.
  if (/^\d{4}-\d{2}-\d{2}$/.test(text)) return `${text}T00:00:00+00:00`;
  return text;
}

function ingestCard() {
  const sourceId = el('input', { class: 'mono', placeholder: 'sec-10k-acme-2025', maxlength: '1000' });
  const published = el('input', { class: 'mono', placeholder: '2025-11-04' });
  const content = el('textarea', { placeholder: 'Paste the full original text here.', maxlength: '16000', style: 'min-height:150px' });
  const problem = el('p', { class: 'muted' });

  const body = el('div', { class: 'disclosure' }, [
    el('div', { class: 'fields' }, [
      field('Source id', sourceId, 'Any short unique handle you will recognise later.'),
      field('Published', published, 'ISO date, stored as UTC. Leave blank if unknown.', true),
    ]),
    field('Document text', content),
    el('div', {}, [btn('Add document', async () => {
      problem.textContent = '';
      try {
        const result = await post('/api/control/ingest', {
          source_id: sourceId.value.trim(),
          published_at: isoDate(published.value),
          content: content.value,
        });
        flash(result.duplicate
          ? 'That exact document is already stored. Nothing was added.'
          : `Added ${result.source_id}. The pipeline traces claims back to ${short(result.content_hash, 8)}.`);
        state.showIngest = false;
        await refresh();
      } catch (err) { reportInto(problem)(err); }
    })]),
    problem,
  ]);

  return card([
    el('div', { class: 'head-row' }, [
      el('div', { class: 'stack' }, [
        el('h2', { class: 'card-title', text: 'Add a document' }),
        el('p', { class: 'card-lede', text: 'Paste the original text and give it a stable id. A URL is stored as a label only — nothing is ever downloaded.' }),
      ]),
      btn(state.showIngest ? 'Close' : 'Paste a document', () => {
        state.showIngest = !state.showIngest;
        refresh();
      }, 'secondary small'),
    ]),
    state.showIngest ? body : null,
  ]);
}

/* ---------- pipeline ---------- */

function stepState(report) {
  const tasks = (report && report.tasks) || [];
  if (tasks.some((t) => t.state === 'leased')) return ['working', C.green];
  if (tasks.some((t) => t.state === 'pending')) return ['waiting', C.amber];
  if (tasks.some((t) => t.state === 'blocked')) return ['blocked', C.red];
  if (tasks.some((t) => t.state === 'failed')) return ['failed', C.red];
  if (tasks.length) return ['done', C.slate];
  return ['idle', C.dim];
}

function renderPipeline(reports) {
  const byRole = {};
  (reports || []).forEach((report) => { byRole[report.role] = report; });
  const selected = state.role && byRole[state.role]
    ? state.role
    : (STEPS.find((step) => (byRole[step.id] || {}).open_task) || STEPS[0]).id;
  state.role = selected;

  const steps = el('div', { class: 'steps' }, STEPS.map((step) => {
    const report = byRole[step.id] || {};
    const [label, color] = stepState(report);
    const prompt = report.active_prompt ? short(report.active_prompt.id) : 'none';
    return el('button', {
      class: step.id === selected ? 'step active' : 'step',
      type: 'button',
      onclick: () => { state.role = step.id; state.openTask = null; location.hash = `pipeline/${step.id}`; },
    }, [
      el('span', { class: 'num', text: step.num }),
      el('span', { class: 'stack' }, [
        el('span', { class: 'title' }, [
          el('span', { class: 't', text: step.title }),
          el('span', { class: 'state-chip', text: label, style: `color:${color}` }),
          step.blinded ? el('span', { class: 'state-chip blinded', text: 'blinded' }) : null,
        ]),
        el('span', { class: 'desc', text: step.desc }),
        el('span', {
          class: 'stats',
          text: `${step.id} · ${plural(report.attempt_count || 0, 'attempt')} · ${plural(report.error_count || 0, 'rejection')} · prompt ${prompt}`,
        }),
      ]),
    ]);
  }));

  page([
    pageHead('Pipeline', 'Six steps every cycle passes through, in order. These are stages of work, not six separate bots.'),
    el('div', { class: 'split pipeline' }, [steps, stepDetail(STEPS.find((s) => s.id === selected), byRole[selected] || {})]),
  ]);
}

function stepDetail(step, report) {
  const [label, color] = stepState(report);
  const open = (report.tasks || []).filter((task) => ['pending', 'leased', 'blocked'].includes(task.state));
  const memory = memoryRows(report);
  const errors = report.submission_errors || [];

  return card([
    el('div', { class: 'stack', style: 'display:flex;flex-direction:column;gap:5px' }, [
      eyebrow('Step detail'),
      el('h2', { style: 'font-size:18px', text: step.title }),
      el('div', { class: 'note', text: step.id }),
    ]),
    step.blinded
      ? el('div', { class: 'notice inline', text: 'Opening a packet here is for your audit only. The reviewer never sees upstream interpretations.' })
      : null,
    rows([
      drow('State', label, color),
      drow('Attempts', String(report.attempt_count || 0)),
      drow('Rejected submissions', String(report.error_count || 0)),
      drow('Active prompt', report.active_prompt ? short(report.active_prompt.id, 16) : 'none'),
      drow('Model', report.route && report.route.model ? `${report.route.provider}:${report.route.model}` : 'unmapped'),
      drow('Key', report.route && report.route.has_key ? `…${report.route.key_hint}` : 'not set'),
    ]),
    el('div', { class: 'col', style: 'gap:9px' }, [
      el('div', { class: 'block-title', text: 'Open tasks' }),
      open.length
        ? el('div', { class: 'col', style: 'gap:6px' }, open.map((task) => taskBlock(task)))
        : el('p', { class: 'muted', text: 'Nothing queued for this step.' }),
    ]),
    el('div', { class: 'col', style: 'gap:9px' }, [
      el('div', { class: 'block-title' }, [txt('Working memory '), el('span', { text: '· versioned' })]),
      memory.length ? rows(memory) : el('p', { class: 'muted', text: 'Empty.' }),
    ]),
    el('div', { class: 'col', style: 'gap:9px' }, [
      el('div', { class: 'block-title', text: 'Error lineage' }),
      errors.length
        ? el('div', { class: 'col', style: 'gap:6px' }, errors.map((error) => el('div', {
          class: 'err', text: `${error.code} · ${short(error.task_id, 18)} · ${stamp(error.created_at)}`,
        })))
        : el('p', { class: 'muted', text: 'None recorded.' }),
    ]),
  ]);
}

function memoryRows(report) {
  const history = report.memory_history || [];
  return (report.memory_current || []).map((current) => {
    const entry = history.find((row) => row.candidate_id === current.candidate_id && row.version === current.version);
    const value = entry && entry.memory ? entry.memory : '(blank)';
    return drow(`${current.candidate_id} v${current.version}`, value.length > 90 ? value.slice(0, 90) + '…' : value);
  });
}

function taskBlock(task) {
  const key = task.task_id;
  const isOpen = state.openTask === key;
  const node = el('div', { class: 'task' }, [
    el('button', {
      type: 'button',
      onclick: () => { state.openTask = isOpen ? null : key; refresh(); },
    }, [
      el('span', { class: 'txt', text: task.reason || `${task.state} · ${task.cycle_id ? short(task.cycle_id, 16) : 'no cycle'}` }),
      el('span', { class: 'meta', text: `${short(task.task_id, 20)} · ${task.state} · tap for the packet` }),
    ]),
  ]);
  if (isOpen) {
    node.append(el('div', { class: 'packet' }, [
      el('div', { class: 'sub-eyebrow', text: 'Immutable packet' }),
      drow('state', task.state),
      drow('worker', task.worker_id || '—'),
      drow('packet_hash', short(task.packet_hash, 16)),
      drow('result_hash', short(task.result_hash, 16)),
      drow('cycle', short(task.cycle_id, 16)),
      el('div', { style: 'padding-top:9px' }, [
        el('button', {
          class: 'btn link', type: 'button', text: 'Open the full packet',
          onclick: () => { location.hash = `task/${task.task_id}`; },
        }),
      ]),
    ]));
  }
  return node;
}

function renderTask(task) {
  page([
    el('div', {}, [el('button', {
      class: 'btn link', type: 'button', text: '← Back to the pipeline',
      onclick: () => go('pipeline'),
    })]),
    pageHead(task.role, `Saved packet and result for ${task.task_id}.`),
    task.blinding ? el('div', { class: 'notice inline', text: task.blinding }) : null,
    card([
      eyebrow('Identity'),
      rows([
        drow('Task', task.task_id),
        drow('State', task.state),
        drow('Worker', task.worker_id || '—'),
        drow('Packet hash', task.packet_hash || '—'),
        drow('Result hash', task.result_hash || '—'),
        task.reason ? drow('Reason', task.reason) : null,
      ]),
    ]),
    card([
      eyebrow('Frozen packet'),
      el('pre', { class: 'mono', style: 'margin:0;white-space:pre-wrap;word-break:break-word;font-size:12px;color:#c9c2b6', text: JSON.stringify(task.packet, null, 2) }),
    ]),
    card([
      eyebrow('Result'),
      el('pre', { class: 'mono', style: 'margin:0;white-space:pre-wrap;word-break:break-word;font-size:12px;color:#c9c2b6', text: task.result ? JSON.stringify(task.result, null, 2) : 'not submitted' }),
    ]),
  ]);
}

/* ---------- ideas ---------- */

function renderIdeas(data) {
  const freeze = (state.overview && state.overview.freeze) || {};
  const families = data.families || [];
  const links = data.cycle_links || [];
  const retros = data.retrospectives || [];

  const cards = families.map((family) => {
    const linked = links.filter((link) => link.family_id === family.family_id).map((link) => link.cycle_id);
    const mine = retros.filter((retro) => retro.family_id === family.family_id);
    const verified = family.frozen_plan_hash && freeze.ok && family.frozen_plan_hash === freeze.sha256;
    return card([
      el('div', { class: 'family-head' }, [
        el('div', { class: 'col', style: 'gap:6px' }, [
          el('div', { class: 'family-id', text: family.candidate_id }),
          el('div', { class: 'note', text: `Recorded ${day(family.created_at)}` }),
        ]),
        el('span', {
          class: verified ? 'pill ok' : family.frozen_plan_hash ? 'pill warn' : 'pill off',
          text: verified ? 'plan verified' : family.frozen_plan_hash ? 'plan hash differs' : 'no plan hash',
        }),
      ]),
      el('p', { class: 'mechanism', text: family.mechanism_summary }),
      el('div', { class: 'facts' }, [
        fact('Frozen plan hash', short(family.frozen_plan_hash, 12)),
        fact('Status', family.status),
        fact('Linked cycles', linked.length ? linked.map((id) => short(id, 14)).join(', ') : 'none'),
        fact('Family id', short(family.family_id, 18)),
      ]),
      mine.length
        ? el('div', { class: 'section-top' }, [
          eyebrow('What slowed it down'),
          ...mine.map((retro) => el('div', { class: 'inset' }, [
            el('span', { class: 'txt', text: retro.bottleneck }),
            el('span', { class: 'meta', text: `${retro.cycle_id ? short(retro.cycle_id, 16) + ' · ' : ''}recorded ${day(retro.created_at)}` }),
          ])),
        ])
        : null,
    ]);
  });

  const familyInput = el('input', { class: 'mono', placeholder: 'family_… or paste from above' });
  const cycleInput = el('input', { class: 'mono', placeholder: 'cycle_…' });
  const bottleneck = el('textarea', {
    placeholder: 'e.g. The auditor rejected three submissions for untraceable figures, so the cycle spent its claims on rework.',
    maxlength: '4000', style: 'min-height:100px',
  });
  const problem = el('p', { class: 'muted' });

  const retroCard = card([
    el('div', { class: 'stack', style: 'display:flex;flex-direction:column;gap:5px' }, [
      el('h2', { class: 'card-title', text: 'Record a retrospective' }),
      el('p', { class: 'card-lede', text: 'Note what bottlenecked a cycle while it is still fresh.' }),
    ]),
    el('div', { class: 'fields' }, [
      field('Idea family', familyInput),
      field('Cycle', cycleInput, null, true),
    ]),
    field('What was the bottleneck?', bottleneck),
    el('div', {}, [btn('Save retrospective', async () => {
      problem.textContent = '';
      try {
        await post('/api/families/retrospective', {
          family_id: familyInput.value.trim(),
          cycle_id: cycleInput.value.trim() || null,
          bottleneck: bottleneck.value,
        });
        await refresh();
      } catch (err) { reportInto(problem)(err); }
    }, 'secondary')]),
    problem,
  ]);

  page([
    pageHead('Ideas', 'One entry per idea family: what the mechanism is, which plan it was frozen against, and which cycles touched it. No similarity search yet, so nothing is matched for you.'),
    families.length
      ? el('div', { class: 'col' }, cards)
      : el('div', { class: 'empty tall' }, [
        el('strong', { text: 'No ideas recorded yet' }),
        el('div', { style: 'max-width:46ch', text: 'Seed the CEF cycle and B3-H1-v1 lands here with its mechanism text and the frozen-plan hash.' }),
        btn('Seed a research cycle', () => go('status')),
      ]),
    families.length ? retroCard : null,
  ]);
}

function fact(key, value) {
  return el('div', { class: 'fact' }, [
    el('span', { class: 'k', text: key }),
    el('span', { class: 'v', text: value }),
  ]);
}

/* ---------- budget ---------- */

function renderBudget(spend, env) {
  const ledger = spend.ledger || {};
  const overview = state.overview || {};
  const attempts = ledger.attempts || [];
  const spentUsd = (ledger.spent && ledger.spent.usd) || 0;
  const limitUsd = (ledger.limit && ledger.limit.usd) || 0;

  const notice = ledger.blocked
    ? el('div', { class: 'notice' }, [
      el('div', { class: 'title' }, [dot(C.amber), txt('Paid work is blocked')]),
      el('p', { class: 'body', text: `${blockedReason(ledger)} An allowance cannot be raised in place — you open a new period instead. Any attempt with an unknown cost also blocks new admissions until you reconcile it.` }),
      el('div', { class: 'foot', text: 'This console cannot set, raise, or bypass an allowance. A new period is opened through the controller.' }),
    ])
    : el('div', { class: 'notice ok' }, [
      el('div', { class: 'title' }, [dot(C.green), txt('Paid work is admitted')]),
      el('p', { class: 'body', text: `Period ${ledger.period_id} allows ${money(ledger.limit)}. Each dispatch reserves its cap first and settles the real cost, so an unknown cost stops the next admission rather than overspending.` }),
      el('div', { class: 'foot' }, [
        overview.provider_dispatch
          ? btn('Dispatch one packet', dispatchOne, 'secondary small')
          : txt('No role has both a mapped model and a key, so nothing can be dispatched yet.'),
      ]),
    ]);

  const cells = [
    ['Allowed', money(ledger.limit), ledger.period_id ? `period ${ledger.period_id}` : 'no period open', null],
    ['Spent', money(ledger.spent), attempts.length ? `${plural(attempts.length, 'attempt')} recorded` : 'nothing dispatched', null],
    ['Reserved', money(ledger.reserved), 'held for in-flight work', null],
    ['Available', money(ledger.available), 'allowed minus spent and reserved', C.amber],
    ['Unknown costs', String(ledger.unknown_count || 0), 'each one blocks new work', ledger.unknown_count ? C.red : C.green],
  ].map(([key, value, cap, color]) => el('div', { class: 'cell' }, [
    el('span', { class: 'k', text: key }),
    el('span', { class: 'v', text: value, style: color ? `color:${color}` : null }),
    el('span', { class: 'cap', text: cap }),
  ]));

  const ledgerCard = card([
    eyebrow('Ledger', `period · ${ledger.period_id || 'none open'}`),
    el('div', { class: 'figure' }, [
      el('span', { class: 'amount', text: money(ledger.spent) }),
      el('span', { class: 'of', text: `spent of ${money(ledger.limit)} allowed` }),
    ]),
    el('div', { class: 'bar', style: 'height:9px;border-radius:5px' }, [
      el('i', { style: `width:${limitUsd ? Math.min(100, Math.round((spentUsd / limitUsd) * 100)) : 0}%` }),
    ]),
    el('div', { class: 'cells' }, cells),
  ]);

  const attemptsCard = card([
    el('div', { class: 'stack', style: 'display:flex;flex-direction:column;gap:5px' }, [
      el('h2', { class: 'card-title', text: 'Attempts' }),
      el('p', { class: 'card-lede', text: 'Every paid attempt with its cap, its real cost, and what the provider actually returned.' }),
    ]),
    attempts.length
      ? el('div', { class: 'tbl' }, [
        el('div', { class: 'th' }, [
          el('span', { class: 'grow', text: 'Attempt' }),
          el('span', { class: 'w100', text: 'State' }),
          el('span', { class: 'w80', text: 'Max' }),
          el('span', { class: 'w80', text: 'Actual' }),
          el('span', { class: 'w110', text: 'Provider req' }),
        ]),
        ...attempts.map((attempt) => el('div', { class: 'tr' }, [
          el('span', { class: 'grow', text: attempt.attempt_id }),
          el('span', { class: 'w100', text: attempt.state }),
          el('span', { class: 'w80', text: money({ usd: attempt.maximum_microusd / 1e6 }) }),
          el('span', { class: 'w80', text: attempt.actual_microusd === null ? '—' : money({ usd: attempt.actual_microusd / 1e6 }) }),
          el('span', { class: 'w110', text: short(attempt.provider_request_id, 12) }),
        ])),
      ])
      : empty(['No attempts recorded.', 'Nothing has been dispatched to a provider.']),
  ]);

  page([
    pageHead('Budget', 'Fail-closed by design. If a cost cannot be accounted for, new work is refused rather than allowed through.'),
    notice,
    ledgerCard,
    attemptsCard,
    env.writable ? envCard(env) : card([
      el('h2', { class: 'card-title', text: 'Provider keys · .env' }),
      el('p', { class: 'card-lede', text: 'This process was started before the console could write .env. Restart it with py -3 go.py --mode dashboard, then come back here to paste a key.' }),
    ]),
  ]);
}

async function dispatchOne() {
  try {
    const result = await post('/api/control/dispatch', {});
    flash(`Sent one ${result.role} packet to ${result.provider}:${result.model}. Decision: ${result.decision || 'none'}.`);
  } catch (err) {
    flash(err.message || String(err));
  }
  await refresh();
}

/* One key per vendor. Saving a key seeds that vendor’s planned model ids
 * (Sol + Astra share the OpenAI key). Role dropdowns write provider:model
 * and reuse the same key. The console cannot raise spend. */
const VENDOR_TITLE = { openai: 'OpenAI', anthropic: 'Anthropic', xai: 'xAI', muse: 'Muse (Meta)' };
const VENDOR_ORDER = ['openai', 'anthropic', 'xai', 'muse'];

function envCard(env) {
  const models = env.models || [];
  const stack = env.stack || [];
  const routeProblem = el('p', { class: 'muted' });

  function specLabel(spec) {
    const hit = stack.find((item) => item.spec === spec || `${item.provider}:${item.model}` === spec);
    return hit ? `${hit.label} · ${spec}` : spec;
  }

  function plannedOptions() {
    const seen = new Set();
    const options = [];
    stack.forEach((item) => {
      const spec = item.model ? `${item.provider}:${item.model}` : item.spec;
      if (!spec || seen.has(spec)) return;
      seen.add(spec);
      options.push({ spec, label: `${item.label} · ${spec}` });
    });
    models.forEach((item) => {
      if (seen.has(item.spec)) return;
      seen.add(item.spec);
      options.push({ spec: item.spec, label: specLabel(item.spec) });
    });
    return options;
  }

  async function saveVendor(name, keyInput, baseInput, problem) {
    problem.textContent = '';
    const meta = env.providers[name];
    if (!meta) { problem.textContent = 'Unknown vendor.'; return; }
    const secret = (env.writable || []).find((row) => row.key === meta.key);
    const values = {};
    const pasted = (keyInput.value || '').replace(/\s+/g, '');
    if (pasted) values[meta.key] = pasted;
    else if (!(secret && secret.set)) { problem.textContent = 'Paste that vendor’s key.'; return; }
    if (baseInput && baseInput.value.trim()) values[meta.base] = baseInput.value.trim();
    try {
      await post('/api/env', { values });
      state.focusVendor = name;
      const hint = pasted ? ` …${pasted.slice(-4)}` : '';
      flash(`Saved ${VENDOR_TITLE[name] || name} key${hint}. The password box stays blank on purpose — look for the green last-four.`);
      await refresh();
      const row = document.getElementById(`vendor-${name}`);
      if (row) row.scrollIntoView({ block: 'center' });
    } catch (err) { reportInto(problem)(err); }
  }

  function bindSecretField(input) {
    input.addEventListener('paste', (ev) => {
      const text = ev.clipboardData ? ev.clipboardData.getData('text') : '';
      if (!text) return;
      ev.preventDefault();
      input.value = text.replace(/\s+/g, '');
    });
  }

  const vendorRows = VENDOR_ORDER.map((name) => {
    const meta = env.providers[name];
    if (!meta) return null;
    const jobs = stack.filter((item) => item.provider === name);
    const secret = (env.writable || []).find((row) => row.key === meta.key);
    const hasKey = Boolean(secret && secret.set);
    const keyInput = el('input', {
      type: 'password', autocomplete: 'off', spellcheck: 'false',
      placeholder: hasKey ? `key …${secret.hint} — paste to replace` : 'paste the API key, then Save key',
    });
    bindSecretField(keyInput);
    const needBase = name === 'muse' || meta.custom;
    const baseInput = needBase
      ? el('input', {
        class: 'mono',
        placeholder: 'https://api.meta.ai/v1',
        value: name === 'muse' ? 'https://api.meta.ai/v1' : '',
      })
      : null;
    const problem = el('p', { class: 'muted' });
    keyInput.addEventListener('keydown', (ev) => {
      if (ev.key === 'Enter') {
        ev.preventDefault();
        saveVendor(name, keyInput, baseInput, problem);
      }
    });
    const focused = state.focusVendor === name;
    if (focused) setTimeout(() => keyInput.focus(), 0);
    return el('div', {
      id: `vendor-${name}`,
      class: 'disclosure',
      style: focused ? 'border-color: var(--amber)' : null,
    }, [
      el('div', { class: 'head-row' }, [
        el('div', { class: 'stack' }, [
          el('span', { class: 'lbl', text: VENDOR_TITLE[name] || name }),
          el('span', { class: 'meta', style: 'font-family:var(--mono);font-size:11px;color:var(--dim-3)', text: jobs.map((job) => `${job.label} (${job.model})`).join(' · ') }),
        ]),
        el('span', { class: 'note', style: hasKey ? `color:${C.green}` : `color:${C.amber}`, text: hasKey ? `key …${secret.hint}` : 'no key' }),
      ]),
      el('div', { class: 'fields' }, [
        field('API key', keyInput, 'Paste, then click Save key. The box clears after a save; a green last-four means it stuck.', true),
        baseInput ? field('Base URL', baseInput, 'Muse defaults to Meta Model API.', name === 'muse') : null,
      ]),
      el('div', { class: 'actions' }, [
        btn(hasKey ? 'Update key' : 'Save key', () => saveVendor(name, keyInput, baseInput, problem)),
      ]),
      problem,
    ]);
  });

  const hostProblem = el('p', { class: 'muted' });
  const alias = el('input', { class: 'mono', placeholder: 'groq, local…' });
  const kind = el('select', {}, [
    el('option', { value: 'openai', text: 'OpenAI-compatible' }),
    el('option', { value: 'anthropic', text: 'Anthropic' }),
  ]);
  const hostModel = el('input', { class: 'mono', placeholder: 'callable model id' });
  const hostKey = el('input', { type: 'password', autocomplete: 'off', spellcheck: 'false', placeholder: 'paste the key' });
  bindSecretField(hostKey);
  const hostBase = el('input', { class: 'mono', placeholder: 'https://api.example.com/v1' });
  const hostForm = el('div', { class: 'disclosure' }, [
    el('p', { class: 'card-lede', text: 'Only for a host that is not OpenAI, Anthropic, xAI, or Muse.' }),
    el('div', { class: 'fields' }, [
      field('Name', alias, 'Letters and digits only.'),
      field('API style', kind),
      field('Model id', hostModel),
      field('API key', hostKey, null, true),
      field('Base URL', hostBase, 'https, or http on localhost.'),
    ]),
    el('div', { class: 'actions' }, [
      btn('Save host', async () => {
        hostProblem.textContent = '';
        const vendor = alias.value.trim().toLowerCase();
        const id = hostModel.value.trim();
        if (!/^[a-z][a-z0-9]{0,20}$/.test(vendor)) {
          hostProblem.textContent = 'Name must start with a letter and be at most 21 letters or digits.';
          return;
        }
        if (!id || !hostBase.value.trim()) { hostProblem.textContent = 'Model id and base URL are required.'; return; }
        const prefix = `PROVIDER_${vendor.toUpperCase()}_`;
        const listed = (env.writable || []).find((row) => row.key === 'RESEARCH_PROVIDERS');
        const aliases = (listed && listed.value ? listed.value.split(',') : []).map((part) => part.trim()).filter(Boolean);
        if (!aliases.includes(vendor)) aliases.push(vendor);
        const catalog = models.map((item) => item.spec);
        const spec = `${vendor}:${id}`;
        if (!catalog.includes(spec)) catalog.push(spec);
        const values = {
          RESEARCH_PROVIDERS: aliases.join(','),
          [prefix + 'KIND']: kind.value,
          [prefix + 'BASE_URL']: hostBase.value.trim(),
          RESEARCH_MODELS: catalog.join(','),
        };
        if (hostKey.value.trim()) values[prefix + 'API_KEY'] = hostKey.value.replace(/\s+/g, '');
        try {
          await post('/api/env', { values });
          state.showHost = false;
          flash(`Added ${spec}.`);
          await refresh();
        } catch (err) { reportInto(hostProblem)(err); }
      }),
      btn('Cancel', () => { state.showHost = false; refresh(); }, 'secondary'),
    ]),
    hostProblem,
  ]);

  const options = plannedOptions();
  const routeRows = (env.routes || []).map((route) => {
    const current = route.configured ? `${route.provider}:${route.model}` : '';
    const select = el('select', { class: 'mono' }, [
      el('option', { value: '', text: 'unmapped' }),
      ...options.map((item) => el('option', {
        value: item.spec, text: item.label, selected: item.spec === current,
      })),
      current && !options.some((item) => item.spec === current)
        ? el('option', { value: current, text: specLabel(current), selected: true })
        : null,
    ]);
    select.addEventListener('change', async () => {
      routeProblem.textContent = '';
      const spec = select.value;
      const values = { [env.roles[route.role]]: spec };
      if (spec && !models.some((item) => item.spec === spec)) {
        values.RESEARCH_MODELS = [...models.map((item) => item.spec), spec].join(',');
      }
      try {
        await post('/api/env', { values });
        flash(spec ? `${route.role} → ${specLabel(spec)}` : `${route.role} unmapped`);
        await refresh();
      } catch (err) { reportInto(routeProblem)(err); }
    });
    return field(
      route.role,
      select,
      route.configured && !route.has_key
        ? `Needs the ${VENDOR_TITLE[route.provider] || route.provider} key above`
        : null,
    );
  });

  return card([
    el('div', { class: 'head-row' }, [
      el('div', { class: 'stack' }, [
        el('h2', { class: 'card-title', text: 'Models · .env' }),
        el('p', { class: 'card-lede', text: 'Paste one key per vendor. Sol and Astra both use the OpenAI key — pick which model each step uses. The console cannot raise spend or silently swap a missing provider.' }),
      ]),
      btn(state.showHost ? 'Close' : 'Another host', () => {
        state.showHost = !state.showHost;
        refresh();
      }, 'secondary small'),
    ]),
    el('p', { class: 'muted', text: 'Green means that vendor’s key is stored. “No key” is a paste field, not a dead label.' }),
    ...vendorRows,
    state.showHost ? hostForm : null,
    el('div', { class: 'disclosure' }, [
      el('p', { class: 'card-lede', text: 'Each pipeline step picks one model. Changing the dropdown saves immediately and keeps the same vendor key.' }),
      el('div', { class: 'fields' }, routeRows),
      routeProblem,
    ]),
    env.budget_configured
      ? null
      : el('p', { class: 'muted', text: 'A key alone does not enable dispatch. Set RESEARCH_BUDGET_PERIOD and RESEARCH_BUDGET_LIMIT_USD in .env yourself and restart, because the console cannot open or raise a spending period.' }),
  ]);
}

/* ---------- history ---------- */

function describe(entry) {
  const known = AUDIT[entry.action];
  if (!known) return { tag: 'Cycles', text: `${entry.action}${entry.detail ? ' · ' + entry.detail : ''}` };
  return { tag: known[0], text: known[1](entry.detail || '') };
}

function renderHistory(data) {
  const log = (data.audit || []).map((entry) => ({ ...entry, ...describe(entry) }));
  const visible = state.filter === 'All' ? log : log.filter((entry) => entry.tag === state.filter);
  const sources = data.sources || [];

  const filters = el('div', { class: 'filters' }, FILTERS.map((name) => el('button', {
    class: state.filter === name ? 'filter active' : 'filter',
    type: 'button', text: name,
    onclick: () => { state.filter = name; refresh(); },
  })));

  const logCard = card([
    visible.length
      ? el('div', {}, visible.map((entry) => el('div', { class: 'event' }, [
        el('span', { class: 'when', text: stamp(entry.created_at) }),
        el('span', { class: 'stack' }, [
          el('span', { class: 'txt', text: entry.text }),
          el('span', { class: 'kind', text: entry.action }),
        ]),
        el('span', { class: 'who', text: entry.actor }),
      ])))
      : empty(['Nothing recorded under this filter.']),
  ], 'log');

  const sourceCard = card([
    el('div', { class: 'stack', style: 'display:flex;flex-direction:column;gap:5px' }, [
      el('h2', { class: 'card-title', text: 'Documents added' }),
      el('p', { class: 'card-lede', text: 'Metadata only — id, date, size, and the hash the pipeline traces claims back to.' }),
    ]),
    sources.length
      ? el('div', { class: 'tbl' }, [
        el('div', { class: 'th' }, [
          el('span', { class: 'grow', text: 'Source id' }),
          el('span', { class: 'w100', text: 'Published' }),
          el('span', { class: 'w80', text: 'Chars' }),
          el('span', { class: 'w110', text: 'Hash' }),
        ]),
        ...sources.map((source) => el('div', { class: 'tr' }, [
          el('span', { class: 'grow', text: source.source_id }),
          el('span', { class: 'w100', text: day(source.published_at) }),
          el('span', { class: 'w80', text: String(source.chars) }),
          el('span', { class: 'w110', text: short(source.content_hash, 8) }),
        ])),
      ])
      : empty(['No documents added yet.']),
  ]);

  page([
    pageHead('History', 'Everything you did in this console, in order. An operator record, not market data.'),
    filters,
    logCard,
    sourceCard,
  ]);
}

/* ---------- routing ---------- */

function flash(message) { state.flash = message; }

function go(tab) {
  location.hash = tab === 'director' ? '' : tab;
  if ((location.hash.replace(/^#/, '') || 'director') === state.tab) route();
}

async function show(tab, extra, keepFlash) {
  if (!keepFlash && tab !== state.tab) { state.flash = ''; state.showStop = false; }
  state.tab = tab;
  state.extra = extra || null;
  try {
    state.overview = await api('/api/overview');
    renderRail();
    if (tab === 'director') {
      renderDirector(await api('/api/messages'));
    } else if (tab === 'status') {
      renderStatus();
    } else if (tab === 'pipeline') {
      if (extra) state.role = extra;
      renderPipeline((await api('/api/roles')).roles);
    } else if (tab === 'ideas') {
      renderIdeas(await api('/api/families'));
    } else if (tab === 'budget') {
      const spend = await api('/api/spend');
      renderBudget(spend, spend.env || {});
    } else if (tab === 'history') {
      renderHistory(await api('/api/audit'));
    } else if (tab === 'task') {
      renderTask(await api(`/api/tasks/${encodeURIComponent(extra)}`));
    }
  } catch (err) {
    if (err.message === 'Your session expired. Sign in again.') return;
    $('main').replaceChildren(el('div', { class: 'page' }, [
      pageHead('Something went wrong', err.message || String(err)),
      el('div', {}, [btn('Try again', () => route(), 'secondary')]),
    ]));
  }
}

const refresh = () => {
  state.restoreScroll = window.scrollY;
  return show(state.tab, state.extra, true);
};

function route() {
  const hash = location.hash.replace(/^#/, '');
  const [head, ...rest] = hash.split('/');
  const tail = rest.join('/');
  if (head === 'task' && tail) return show('task', decodeURIComponent(tail));
  if (head === 'pipeline') return show('pipeline', tail || null);
  return show(VIEWS.includes(head) ? head : 'director');
}

/* ---------- session ---------- */

function showLogin() {
  $('app').classList.add('hidden');
  $('login').classList.remove('hidden');
}

function showApp() {
  $('login').classList.add('hidden');
  $('app').classList.remove('hidden');
}

$('login-form').addEventListener('submit', async (ev) => {
  ev.preventDefault();
  $('login-error').textContent = '';
  try {
    const data = await api('/api/login', { method: 'POST', body: JSON.stringify({ password: $('password').value }) });
    state.csrf = data.csrf;
    state.operator = data.operator || 'james';
    $('password').value = '';
    showApp();
    route();
  } catch (err) {
    $('login-error').textContent = err.message === 'Your session expired. Sign in again.' ? 'Invalid password' : err.message;
  }
});

$('logout').addEventListener('click', async () => {
  try { await post('/api/logout', {}); } catch (err) { /* the cookie is gone either way */ }
  state.csrf = null;
  showLogin();
});

window.addEventListener('hashchange', route);

(async function boot() {
  try {
    const me = await api('/api/me');
    state.csrf = me.csrf;
    state.operator = me.operator || 'james';
    showApp();
    route();
  } catch (err) {
    showLogin();
  }
})();
