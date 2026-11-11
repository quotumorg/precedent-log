// Execute the shipped ESM with a documented SDK facade; no DOM or dependencies.
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const originalNow = Date.now
let now = Date.parse('2026-11-07T12:02:00Z')
Date.now = () => now
const snapshot = {
  state: 'ready', board: 'default', active: 3, total: 3, truncated: false, cap_reached: false,
  last_veto: { id: 'P-1', title: 'schema migrations', at: '2026-11-07T12:00:00Z' },
  rows: [{ id: 'P-1', title: 'schema migrations', keys: ['schema', 'migrations'], status: 'active',
    ruling: 'Use staging.', jobs: ['job-1'], cited_count: 1, veto_count: 2, cap_reached: false, last_veto: '2026-11-07T12:00:00Z',
    receipt: { author: 'desktop:session-example', surface: 'slash', at: '2026-11-07T10:00:00Z', source_task: 'source-card' },
    timeline_total: 4, timeline: [
      { kind: 'saved', at: '2026-11-07T10:00:00Z', task_id: null, detail: '' },
      { kind: 'cite', at: '2026-11-07T11:00:00Z', task_id: 'job-1', detail: 'completed' },
      { kind: 'explain', at: null, task_id: 'old-card', detail: 'block-time' },
      { kind: 'cite', at: '2026-11-07T12:00:00Z', task_id: 'job-2', detail: 'block vetoed' },
    ] }],
}
const retiredRow = row => ({ ...row, status: 'retired', timeline_total: row.timeline_total + 1,
  timeline: [...row.timeline, { kind: 'retired', at: '2026-11-07T12:01:00Z', task_id: null, detail: 'Retired from Desktop' }] })
const encode = data => 'precedent-log rulings v1\n' + JSON.stringify(data)
const sessionOutput = encode(snapshot)
const source = await readFile(new URL('../desktop/plugin.js', import.meta.url), 'utf8')
const transformed = source.replace(
  "import { host, STATUSBAR_AREAS, ROUTES_AREA, SIDEBAR_NAV_AREA, Button, Badge, EmptyState } from '@hermes/plugin-sdk'",
  'const { host, STATUSBAR_AREAS, ROUTES_AREA, SIDEBAR_NAV_AREA, Button, Badge, EmptyState } = globalThis.precedentSDK',
).replace("import { createElement as h, useSyncExternalStore } from 'react'", 'const { h, useSyncExternalStore } = globalThis.precedentSDK')
const atom = (initial) => {
  let value = initial
  const listeners = new Set()
  return {
    get: () => value,
    subscribe(fn) { listeners.add(fn); fn(); return () => listeners.delete(fn) },
    set(next) { value = next; for (const fn of listeners) fn() },
    listeners,
  }
}
const host = {
  state: {
    focusedSessionId: atom(null), focusedSessionProfile: atom('default'), gateway: atom('open'),
    focusedSessionOwner: atom({ connectionId: 'local', profile: 'default' }),
  },
  profileRoutes: async () => [
    { connectionId: 'local', profile: 'default' },
    { connectionId: 'remote', profile: 'other' },
    { connectionId: 'second-remote', profile: 'other' },
  ],
  requestProfile: (route, method, params, timeout) => {
    assert.equal(route.connectionId, host.state.focusedSessionOwner.get().connectionId)
    assert.equal(timeout, 2000)
    assert.equal(method, 'slash.exec')
    assert.ok(params.command === '/rulings list --json' || params.command.startsWith('/ruling retire P-1 '))
    return host.request(method, params)
  },
  request: async () => ({ type: 'exec', output: sessionOutput }),
}
globalThis.precedentSDK = { host, STATUSBAR_AREAS: { right: 'statusBar.right' }, ROUTES_AREA: 'routes', SIDEBAR_NAV_AREA: 'nav',
  Button: props => ({ tag: 'button', props, children: props.children }),
  Badge: props => ({ tag: 'span', props: { ...props, 'data-slot': 'badge' }, children: props.children }),
  EmptyState: props => ({ tag: 'div', props, children: [props.title, props.description] }),
  h: (tag, props, ...children) => typeof tag === 'function' ? tag({ ...props, children: children.flat().filter(x => x !== null) }) : ({ tag, props: props || {}, children: children.flat().filter(x => x !== null) }),
  useSyncExternalStore: (_, get) => get(),
}
const plugin = (await import('data:text/javascript;base64,' + Buffer.from(transformed).toString('base64'))).default
let registrations = 0
let chip = null
let timer = null
let watchdog = null
const disposers = []
const contributions = new Map()
const ctx = {
  register(item) {
    registrations++; contributions.set(item.id, item)
    if (item.area === 'statusBar.right') chip = item
    const dispose = () => { if (chip === item) chip = null; if (contributions.get(item.id) === item) contributions.delete(item.id) }
    disposers.push(dispose); return dispose
  },
  onDispose(fn) { disposers.push(fn) },
  setInterval(fn, ms) {
    assert.ok([1000, 3000].includes(ms))
    if (ms === 3000) timer = fn
    else watchdog = fn
    disposers.push(() => { timer = null; watchdog = null })
  },
}
const settle = () => new Promise(resolve => setImmediate(resolve))
plugin.register(ctx)
const page = () => contributions.get('rulings-page').render()
const dump = node => typeof node === 'object' ? node.children.map(dump).join(' ') : String(node)
const nodes = node => typeof node === 'object' ? [node, ...node.children.flatMap(nodes)] : []
const click = label => {
  const button = nodes(page()).find(n => n.tag === 'button' && dump(n) === label)
  assert.ok(button, label); assert.ok(!button.props.disabled); button.props.onClick()
}
assert.equal(contributions.get('rulings-page').area, 'routes')
assert.equal(contributions.get('rulings-nav').data.label, 'Rulings')
assert.match(dump(page()), /Open any session to load rulings for its profile/)
console.log('PAGE: ' + dump(page()))
assert.equal(chip, null)
let noSessionRequests = 0
const initialRequest = host.request
host.request = async () => { noSessionRequests++; return { type: 'exec', output: sessionOutput } }
await timer()
assert.equal(noSessionRequests, 0)
host.request = initialRequest
host.state.focusedSessionId.set('session-a')
await settle()
assert.equal(chip.data.label, 'Precedent Log · 3 rulings · last veto: P-1 schema migrations, 2 min ago')
assert.equal(chip.area, 'statusBar.right')
assert.ok(chip.data.title.includes('active rulings'))
console.log(chip.data.label)
assert.equal(chip.data.detail, undefined)
assert.equal(chip.data.to, '/precedent-rulings')
assert.match(dump(page()), /P-1 schema migrations/)
assert.match(dump(page()), /Use staging./)
assert.match(dump(page()), /job-1/)
assert.match(dump(page()), /Saved answer receipt: desktop:session-example · slash/)
assert.match(dump(page()), /Source card: source-card/)
assert.match(dump(page()), /not an authenticated approver/)
assert.match(dump(page()), /2026-11-07 11:00:00 UTC\s+· cite · card job-1 · completed/)
assert.match(dump(page()), /time not recorded\s+· explain · card old-card/)
assert.match(dump(page()), /cite · card job-2 · block vetoed/)
assert.ok(nodes(page()).some(n => n.tag === 'ol' && n.props['aria-label'] === 'Timeline for P-1'))
assert.ok(nodes(page()).some(n => n.tag === 'time' && n.props.dateTime === '2026-11-07T11:00:00Z'))
console.log('PAGE: ' + dump(page()))
// Limits disclose omitted history; missing legacy metadata never becomes an identity or time.
host.request = async () => ({ type: 'exec', output: encode({ ...snapshot, rows: [{ ...snapshot.rows[0],
  timeline_total: 80, receipt: { author: '', surface: null, at: null, source_task: '' },
}] }) })
await timer()
assert.match(dump(page()), /Showing 4 of 80 timeline events/)
assert.match(dump(page()), /author not recorded · source not recorded · time not recorded/)
// Full questions wrap on the page; the status retains its independently bounded title.
const longQuestion = 'Which database should we use for the schema migration in the local plan?'
for (const n of [0, 1, 2]) {
  const row = { ...snapshot.rows[0], title: longQuestion, cited_count: n, jobs: n ? ['job-1'] : [], veto_count: n }
  host.request = async () => ({ type: 'exec', output: encode({ ...snapshot, active: n, rows: [row] }) })
  await timer()
  assert.ok(dump(page()).includes(longQuestion))
  assert.ok(dump(page()).includes(`cited by ${n} completed ${n === 1 ? 'job' : 'jobs'}`))
  assert.ok(dump(page()).includes(`Completed ${n === 1 ? 'job' : 'jobs'} (`))
  assert.ok(chip.data.label.includes(`${n} ${n === 1 ? 'ruling' : 'rulings'} ·`))
  assert.ok(nodes(page()).some(x => x.props['data-slot'] === 'badge' && x.props.variant === 'success'))
  const retireButton = nodes(page()).find(x => x.tag === 'button' && dump(x) === 'Retire P-1')
  assert.equal(retireButton.props.variant, 'destructive')
  assert.equal(nodes(page()).find(x => x.tag === 'button' && dump(x) === 'Refresh').props.variant, 'secondary')
  console.log(chip.data.label)
}
host.request = async () => ({ type: 'exec', output: encode({ ...snapshot,
  rows: [{ ...snapshot.rows[0], title: 'x'.repeat(2000) }],
  last_veto: { ...snapshot.last_veto, at: '2026-11-06T12:00:00Z' },
}) })
await timer()
assert.ok(dump(page()).includes('x'.repeat(2000)))
assert.ok(chip.data.label.endsWith('1 day ago'))
assert.ok(nodes(page()).some(x => x.tag === 'article' && x.props.style.overflowWrap === 'anywhere'))
host.request = async () => ({ type: 'exec', output: sessionOutput })
await timer()
const initialChip = chip
const initialRegistrations = registrations
await timer()
assert.equal(chip, initialChip)
assert.equal(registrations, initialRegistrations)
// A board with no recorded veto reports that fact.
host.request = async () => ({ type: 'exec', output: encode({ ...snapshot, last_veto: null }) })
await timer()
assert.equal(chip.data.label, 'Precedent Log · 3 rulings · no veto yet')
console.log(chip.data.label)
host.request = async () => ({ type: 'exec', output: encode({ ...snapshot, cap_reached: true,
  rows: [{ ...snapshot.rows[0], cap_reached: true }] }) })
await timer()
assert.match(chip.data.label, /veto cap reached/)
assert.match(dump(page()), /veto cap reached/)
console.log('PAGE CAP: ' + dump(page()))
// Empty is distinct from absent focus and failed data.
host.request = async () => ({ type: 'exec', output: encode({ state: 'empty', board: 'default' }) })
await timer()
assert.match(dump(page()), /No rulings yet/)
console.log('PAGE: ' + dump(page()))
assert.equal(chip.data.label, 'Precedent Log · 0 rulings · no veto yet')
console.log(chip.data.label)
// Missing state is not a fabricated zero.
host.request = async () => ({ type: 'exec', output: 'Precedent Log status unavailable' })
await timer()
assert.equal(chip, null)
assert.match(dump(page()), /Unavailable/)
console.log('PAGE: ' + dump(page()))
// Confirmation is required, uses the exact board, and re-reads storage.
const writes = []
let retired = false
host.request = async (_, params) => {
  writes.push(params.command)
  if (params.command.startsWith('/ruling retire')) {
    retired = true
    return { type: 'exec', output: 'P-1 retired. 1 completed job cited it: job-1.' }
  }
  return { type: 'exec', output: encode(retired ? { ...snapshot, rows: [retiredRow(snapshot.rows[0])] } : snapshot) }
}
await timer()
writes.length = 0
click('Retire P-1')
assert.equal(writes.length, 0)
assert.match(dump(page()), /Confirm retire P-1/)
const confirmation = nodes(page()).find(x => x.props['aria-label'] === 'Confirm retirement of P-1')
assert.equal(confirmation.props.style.gap, 12)
assert.ok(confirmation.children.some(x => x.props?.style?.gap === 8))
assert.equal(nodes(confirmation).find(x => x.tag === 'button' && dump(x) === 'Confirm retire P-1').props.variant, 'destructive')
click('Cancel')
assert.equal(writes.length, 0)
click('Retire P-1')
click('Confirm retire P-1')
assert.ok(!dump(page()).includes('Use staging.'))
await settle()
assert.deepEqual(writes, ['/ruling retire P-1 Retired from Desktop --board default', '/rulings list --json'])
assert.match(dump(page()), /retired/)
assert.match(dump(page()), /2026-11-07 12:01:00 UTC\s+· retired · Retired from Desktop/)
assert.ok(nodes(page()).some(x => x.props['data-slot'] === 'badge' && x.props.variant === 'muted'))
assert.ok(!nodes(page()).some(n => n.tag === 'button' && dump(n) === 'Retire P-1'))
// A backend error remains visible; the subsequent read remains authoritative.
host.request = async (_, params) => ({ type: 'exec', output: params.command.startsWith('/ruling retire')
  ? 'Store lock is busy' : sessionOutput })
await timer()
click('Retire P-1'); click('Confirm retire P-1')
await settle()
assert.match(dump(page()), /Store lock is busy/)
assert.match(dump(page()), /active/)
// Board switch drops confirmation and the previous row snapshot.
click('Retire P-1')
host.request = async () => ({ type: 'exec', output: encode({ ...snapshot, board: 'other' }) })
await timer()
assert.ok(!dump(page()).includes('Confirm retire P-1'))
// A confirmed write may finish on its original scope; its reply never fills a new profile.
host.request = async () => ({ type: 'exec', output: sessionOutput })
await timer()
click('Retire P-1')
let releaseRetire
const retirementCalls = []
host.request = (_, params) => {
  retirementCalls.push(params.command)
  return new Promise(resolve => { releaseRetire = resolve })
}
click('Confirm retire P-1')
await settle()
host.state.focusedSessionProfile.set('other')
host.state.focusedSessionOwner.set({ connectionId: 'remote', profile: 'other' })
assert.match(dump(page()), /Unavailable/)
host.request = async () => ({ type: 'exec', output: encode({ state: 'empty', board: 'other' }) })
releaseRetire({ type: 'exec', output: 'P-1 retired.' })
await settle()
assert.equal(retirementCalls.length, 1)
assert.match(dump(page()), /No rulings yet/)
assert.ok(!dump(page()).includes('P-1'))
host.state.focusedSessionProfile.set('default')
host.state.focusedSessionOwner.set({ connectionId: 'local', profile: 'default' })
await settle()
// Focus churn cannot accumulate unresolved requests. Latest focus wins after settlement.
const pending = []
host.request = (_, params) => new Promise(resolve => pending.push({ params, resolve }))
const first = timer()
await settle()
for (let i = 0; i < 100; i++) host.state.focusedSessionId.set('session-' + i)
host.state.focusedSessionProfile.set('other')
host.state.focusedSessionOwner.set({ connectionId: 'remote', profile: 'other' })
await settle()
assert.equal(pending.length, 1)
assert.equal(chip, null)
const response = { type: 'exec', output: sessionOutput }
pending[0].resolve(response)
await first
await settle()
assert.equal(pending.length, 2)
assert.equal(pending[1].params.session_id, 'session-99')
assert.equal(pending[1].params.profile, 'other')
assert.equal(chip, null)
pending[1].resolve(response)
await settle()
assert.ok(chip)
const oldSourceRequest = timer()
await settle()
host.state.focusedSessionOwner.set({ connectionId: 'second-remote', profile: 'other' })
assert.equal(chip, null)
pending[2].resolve(response)
await oldSourceRequest
await settle()
assert.equal(chip, null)
pending[3].resolve(response)
await settle()
assert.ok(chip)
host.state.focusedSessionOwner.set(null)
assert.equal(chip, null)
host.request = async () => response
host.state.focusedSessionOwner.set({ connectionId: 'remote', profile: 'other' })
await settle()
// Only bounded output with the protocol header may render.
for (const output of ['header\n' + sessionOutput.split('\n')[1],
  sessionOutput + 'x'.repeat(65536), encode({ ...snapshot, active: -1 }),
  encode({ ...snapshot, rows: [{ ...snapshot.rows[0], title: 'x'.repeat(2001) }] }),
  sessionOutput.replaceAll('2026-11-07', '2026-02-31'),
  sessionOutput.replaceAll('12:00:00', '12:59:00'),
  encode({ ...snapshot, rows: Array(51).fill(snapshot.rows[0]) }),
  encode({ ...snapshot, rows: [{ ...snapshot.rows[0], jobs: ['bad job'] }] }),
  encode({ ...snapshot, rows: [{ ...snapshot.rows[0], ruling: 'x'.repeat(2001) }] }),
  encode({ ...snapshot, rows: [snapshot.rows[0], snapshot.rows[0]] }),
  encode({ ...snapshot, rows: [{ ...snapshot.rows[0], cited_count: 0 }] }),
  ...[
    { timeline: null }, { timeline: [] }, { timeline_total: 0 }, { timeline: Array(53).fill(snapshot.rows[0].timeline[0]) },
    { timeline: [{ ...snapshot.rows[0].timeline[0], at: '2026-02-31T10:00:00Z' }] },
    { timeline: [{ ...snapshot.rows[0].timeline[0], at: '2999-01-01T10:00:00Z' }] },
    { timeline: [{ ...snapshot.rows[0].timeline[0], kind: 'approval' }] },
    { timeline: [snapshot.rows[0].timeline[0], { ...snapshot.rows[0].timeline[1], task_id: 'bad card' }] },
    { timeline: [snapshot.rows[0].timeline[0], { ...snapshot.rows[0].timeline[1], detail: 'x'.repeat(241) }] },
    { timeline: [snapshot.rows[0].timeline[0], snapshot.rows[0].timeline[0]] },
    { status: 'retired' }, { receipt: null },
    { receipt: { ...snapshot.rows[0].receipt, author: 'x'.repeat(161) } },
    { receipt: { ...snapshot.rows[0].receipt, surface: 'authenticated-human' } },
    { receipt: { ...snapshot.rows[0].receipt, at: 'invalid' } },
  ].map(fields => encode({ ...snapshot, rows: [{ ...snapshot.rows[0], ...fields }] })),
  encode({ ...snapshot, extra: '界'.repeat(30000) }),
  encode({ ...snapshot, board: null }),
  'precedent-log rulings v1\nnull']) {
  host.request = async () => ({ type: 'exec', output })
  await timer()
  assert.equal(chip, null)
}
// An unresolved route inventory hides stale data and retains only one operation.
host.request = async () => response
await timer()
assert.ok(chip)
const normalInventory = host.profileRoutes
let releaseRoutes
let routeCalls = 0
host.profileRoutes = () => { routeCalls++; return new Promise(resolve => { releaseRoutes = resolve }) }
const stuck = timer()
await settle()
now += 5000
watchdog()
await timer()
assert.equal(chip, null)
for (let i = 0; i < 100; i++) host.state.focusedSessionId.set('route-' + i)
assert.equal(routeCalls, 1)
host.profileRoutes = normalInventory
releaseRoutes(await normalInventory())
await stuck
await settle()
assert.ok(chip)
// The command itself can hang without a focus change; stale data must hide.
let releaseCommand
host.request = () => new Promise(resolve => { releaseCommand = resolve })
const stuckCommand = timer()
await settle()
now += 5000
watchdog()
await timer()
assert.equal(chip, null)
releaseCommand(response)
await stuckCommand
assert.equal(chip, null)
host.request = async () => response
await timer()
assert.ok(chip)
// A rejected command clears any previously displayed status.
host.request = async () => { throw Error('unavailable') }
await timer()
assert.equal(chip, null)
// Malformed route inventories are contained and never leave a stale chip.
const validInventory = host.profileRoutes
for (const routes of [null, {}, [null]]) {
  host.profileRoutes = async () => routes
  await timer()
  assert.equal(chip, null)
}
host.profileRoutes = validInventory
// Route inventory failure also hides stale data and is contained.
const inventory = host.profileRoutes
host.profileRoutes = async () => { throw Error('route inventory unavailable') }
await timer()
assert.equal(chip, null)
host.profileRoutes = inventory
// A disconnect clears a chip synchronously.
host.request = async () => response
await timer()
assert.ok(chip)
host.state.gateway.set('idle')
assert.equal(chip, null)
host.state.gateway.set('open')
await settle()
assert.ok(chip)
// Actually unload with one command still unresolved.
let releaseOnUnload
host.request = () => new Promise(resolve => { releaseOnUnload = resolve })
const unloading = timer()
await settle()
assert.equal(typeof releaseOnUnload, 'function')
for (const dispose of disposers) dispose()
releaseOnUnload(response)
await unloading
assert.equal(chip, null)
assert.equal(timer, null)
for (const item of Object.values(host.state)) assert.equal(item.listeners.size, 0)
// Replies from earlier generations cannot restore a disposed chip.
for (const item of pending) item.resolve(response)
await settle()
assert.equal(chip, null)
assert.equal(contributions.size, 0)
Date.now = originalNow
console.log('desktop facade checks passed (rendering, no veto, scope churn, routing, stale inventory/command, bounds, exact header, failures, disposal)')
