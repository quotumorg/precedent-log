// Execute the shipped ESM with a documented SDK facade; no DOM or dependencies.
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const originalNow = Date.now
let now = Date.parse('2026-11-07T12:02:00Z')
Date.now = () => now
const sessionOutput = 'precedent-log status v1\nrulings=3; veto=P-1; title=schema migrations; at=2026-11-07T12:00:00Z'
const source = await readFile(new URL('../desktop/plugin.js', import.meta.url), 'utf8')
const transformed = source.replace(
  "import { host, STATUSBAR_AREAS } from '@hermes/plugin-sdk'",
  'const { host, STATUSBAR_AREAS } = globalThis.precedentSDK',
)
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
    assert.equal(params.command, '/rulings status')
    return host.request(method, params)
  },
  request: async () => ({ type: 'exec', output: sessionOutput }),
}
globalThis.precedentSDK = { host, STATUSBAR_AREAS: { right: 'statusBar.right' } }
const plugin = (await import('data:text/javascript;base64,' + Buffer.from(transformed).toString('base64'))).default
let registrations = 0
let chip = null
let timer = null
let watchdog = null
const disposers = []
const ctx = {
  register(item) { registrations++; chip = item; return () => { if (chip === item) chip = null } },
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
assert.equal(chip, null)
host.state.focusedSessionId.set('session-a')
await settle()
assert.equal(chip.data.label, 'Precedent Log · 3 rulings · last veto: P-1 schema migrations, 2 min ago')
assert.equal(chip.area, 'statusBar.right')
assert.ok(chip.data.title.includes('active rulings'))
console.log(chip.data.label)
assert.equal(chip.data.detail, undefined)
const initialChip = chip
const initialRegistrations = registrations
await timer()
assert.equal(chip, initialChip)
assert.equal(registrations, initialRegistrations)
// A board with no recorded veto reports that fact.
host.request = async () => ({ type: 'exec', output: 'precedent-log status v1\nrulings=3; no veto yet' })
await timer()
assert.equal(chip.data.label, 'Precedent Log · 3 rulings · no veto yet')
console.log(chip.data.label)
// Missing state is not a fabricated zero.
host.request = async () => ({ type: 'exec', output: 'Precedent Log status unavailable' })
await timer()
assert.equal(chip, null)
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
  sessionOutput + 'x'.repeat(2048),
  sessionOutput + '\n', sessionOutput.replace('rulings=3', 'rulings=-1'),
  sessionOutput.replace('schema migrations', 'x'.repeat(41)),
  sessionOutput.replace('2026-11-07', '2026-02-31'),
  sessionOutput.replace('12:00:00', '12:59:00')]) {
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
Date.now = originalNow
console.log('desktop facade checks passed (rendering, no veto, scope churn, routing, stale inventory/command, bounds, exact header, failures, disposal)')
