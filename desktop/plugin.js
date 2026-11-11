import { host, STATUSBAR_AREAS, ROUTES_AREA, SIDEBAR_NAV_AREA, Button, Badge, EmptyState } from '@hermes/plugin-sdk'
import { createElement as h, useSyncExternalStore } from 'react'

// SDK runtime.ts:63-66 supplies the host React singleton; no bundled dependency.
const PATH = '/precedent-rulings'
const HEADER = 'precedent-log rulings v1\n'
const LIMIT = 64 * 1024
const idPattern = /^P-[1-9][0-9]{0,8}$/
const boardPattern = /^[a-z0-9][a-z0-9_-]{0,63}$/
const text = (s, limit) => typeof s === 'string' && s.length <= limit && !/[\x00-\x08\x0b-\x1f\x7f-\x9f]/u.test(s)
const plural = (n, singular, many = singular + 's') => n === 1 ? singular : many
const count = n => Number.isSafeInteger(n) && n >= 0
const stamp = s => typeof s === 'string' && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/.test(s)
  && Number.isFinite(Date.parse(s)) && new Date(s).toISOString().replace('.000Z', 'Z') === s && Date.parse(s) <= Date.now()
const recordedTime = s => s === null || stamp(s)
const when = s => s ? s.replace('T', ' ').replace('Z', ' UTC') : 'time not recorded'
const jobPattern = /^[A-Za-z0-9_-]{1,128}$/
const age = s => {
  const seconds = Math.floor((Date.now() - Date.parse(s)) / 1000)
  return seconds < 60 ? 'just now' : seconds < 3600 ? `${Math.floor(seconds / 60)} min ago`
    : seconds < 86400 ? `${Math.floor(seconds / 3600)} hr ago` : `${Math.floor(seconds / 86400)} ${plural(Math.floor(seconds / 86400), 'day')} ago`
}
function parse(result) {
  const output = result?.type === 'exec' ? result.output : null
  if (typeof output !== 'string' || output.length > LIMIT || new TextEncoder().encode(output).length > LIMIT
      || !output.startsWith(HEADER)) throw Error('Unavailable')
  const data = JSON.parse(output.slice(HEADER.length))
  if (!data || !['ready', 'empty', 'no-board', 'unavailable'].includes(data.state)) throw Error('Unavailable')
  if (['no-board', 'unavailable'].includes(data.state)) return { state: data.state }
  if (typeof data.board !== 'string' || !boardPattern.test(data.board)) throw Error('Unavailable')
  if (data.state === 'empty') return { state: 'empty', board: data.board }
  if (!count(data.active) || !count(data.total) || data.active > data.total || typeof data.truncated !== 'boolean' || typeof data.cap_reached !== 'boolean'
      || !Array.isArray(data.rows) || data.rows.length > 50 || data.rows.length > data.total) throw Error('Unavailable')
  const ids = new Set()
  for (const row of data.rows) {
    if (!row || typeof row.id !== 'string' || !idPattern.test(row.id) || ids.has(row.id)
        || !text(row.title, 2000) || !text(row.ruling, 2000) || !['active', 'retired'].includes(row.status)
        || !Array.isArray(row.keys) || row.keys.length > 20 || row.keys.some(k => !text(k, 80))
        || !Array.isArray(row.jobs) || row.jobs.length > 20 || row.jobs.some(j => typeof j !== 'string' || !/^[A-Za-z0-9_-]{1,128}$/.test(j))
        || typeof row.cap_reached !== 'boolean' || !count(row.cited_count) || row.cited_count < row.jobs.length || !count(row.veto_count)
        || (row.last_veto !== null && !stamp(row.last_veto))) throw Error('Unavailable')
    if (!Array.isArray(row.timeline) || row.timeline.length < 1 || row.timeline.length > 52
        || !count(row.timeline_total) || row.timeline_total < row.timeline.length
        || !row.receipt || !text(row.receipt.author, 160) || ![null, 'cli', 'slash'].includes(row.receipt.surface)
        || !recordedTime(row.receipt.at) || !text(row.receipt.source_task, 128)) throw Error('Unavailable')
    let saves = 0, retirements = 0
    for (const event of row.timeline) {
      if (!event || !['saved', 'cite', 'explain', 'retired'].includes(event.kind)
          || !recordedTime(event.at) || !text(event.detail, 240)) throw Error('Unavailable')
      if (event.kind === 'saved' || event.kind === 'retired') {
        if (event.task_id !== null) throw Error('Unavailable')
        if (event.kind === 'saved') saves++
        else retirements++
      } else if (typeof event.task_id !== 'string' || !jobPattern.test(event.task_id)) throw Error('Unavailable')
    }
    if (saves !== 1 || retirements !== (row.status === 'retired' ? 1 : 0)) throw Error('Unavailable')
    ids.add(row.id)
  }
  if (data.last_veto !== null && (!data.last_veto || !idPattern.test(data.last_veto.id)
      || !text(data.last_veto.title, 40) || !stamp(data.last_veto.at))) throw Error('Unavailable')
  return data
}

export default {
  id: 'precedent-log', name: 'Precedent Log',
  register(ctx) {
    let model = { state: 'no-board', error: '', confirm: null, busy: false }
    const listeners = new Set()
    let disposeChip = () => {}
    let displayedLine = null
    let generation = 0
    let pending = null
    let disposed = false
    let lastSuccess = null
    const scope = () => JSON.stringify([host.state.focusedSessionId.get(), host.state.focusedSessionProfile.get(),
      host.state.gateway.get(), host.state.focusedSessionOwner.get()])
    const publish = next => { model = next; for (const fn of listeners) fn() }
    const clearChip = () => { disposeChip(); disposeChip = () => {}; displayedLine = null }
    const clear = (state = 'unavailable', error = '') => {
      clearChip(); lastSuccess = null
      publish({ state, error, confirm: null, busy: false })
    }
    const chip = data => {
      if (!['ready', 'empty'].includes(data.state)) { clearChip(); return }
      const veto = data.last_veto
      const last = veto ? `last veto: ${veto.id} ${veto.title}, ${age(veto.at)}` : 'no veto yet'
      const active = data.state === 'empty' ? 0 : data.active
      const line = `Precedent Log · ${active} ${plural(active, 'ruling')} · ${last}${data.cap_reached ? ' · veto cap reached' : ''}`
      if (line === displayedLine) return
      clearChip()
      disposeChip = ctx.register({ id: 'precedent-status', area: STATUSBAR_AREAS.right, order: 130,
        data: { id: 'precedent-status', label: line, to: PATH,
          title: 'Counts active rulings and the latest recorded gate veto on the current board in the focused profile.' } })
      displayedLine = line
    }
    const refresh = async (retirement = null) => {
      const key = scope()
      const session = host.state.focusedSessionId.get()
      const profile = host.state.focusedSessionProfile.get()
      const owner = host.state.focusedSessionOwner.get()
      if (disposed) return
      if (!session) { clear('no-board'); return }
      if (!owner || owner.profile !== profile || host.state.gateway.get() !== 'open') { clear(); return }
      if (pending) {
        if (Date.now() - pending.started >= 5000) clear()
        return
      }
      const ticket = { key, generation, started: Date.now() }
      const current = () => !disposed && ticket.generation === generation && scope() === key
      const fresh = () => current() && Date.now() - ticket.started < 5000
      pending = ticket
      if (retirement) { clear(); publish({ ...model, busy: true }) }
      let error = model.error
      try {
        const routes = await host.profileRoutes()
        if (!fresh()) { if (current()) clear(); return }
        const route = routes.find(item => item.connectionId === owner.connectionId && item.profile === owner.profile)
        if (!route) throw Error('Unavailable')
        const request = command => host.requestProfile(route, 'slash.exec', {
          session_id: session, profile, command,
        }, 2000)
        if (retirement) {
          // Board pinned from the confirmed snapshot, never inferred again by the write.
          try {
            const result = await request(`/ruling retire ${retirement.id} Retired from Desktop --board ${retirement.board}`)
            if (!fresh()) { if (current()) clear('unavailable', 'Retirement result unavailable; re-read before retrying.'); return }
            const output = result?.type === 'exec' && text(result.output, 4096) ? result.output : ''
            if (!output.startsWith(`${retirement.id} retired.`)) error = output.split('\n')[0].slice(0, 240) || 'Retirement unavailable'
            else error = ''
          } catch { error = 'Retirement unavailable; re-read before retrying.' }
          if (!fresh()) { if (current()) clear('unavailable', error); return }
        }
        const data = parse(await request('/rulings list --json'))
        if (!fresh()) { if (current()) clear('unavailable', error); return }
        const confirm = !retirement && model.board === data.board ? model.confirm : null
        if ((retirement?.board || model.board) && (retirement?.board || model.board) !== data.board) error = ''
        publish({ ...data, error, confirm, busy: false })
        chip(data)
        lastSuccess = Date.now()
      } catch {
        if (current()) clear('unavailable', error)
      } finally {
        if (pending === ticket) pending = null
        if (!disposed && ticket.generation !== generation) void refresh()
      }
    }
    const confirmRetire = () => {
      const value = model.confirm
      if (!value || model.state !== 'ready' || pending || lastSuccess === null || Date.now() - lastSuccess >= 5000
          || value.key !== scope() || value.board !== model.board
          || !model.rows.some(r => r.id === value.id && r.status === 'active')) return
      void refresh(value)
    }
    function Page() {
      const view = useSyncExternalStore(fn => { listeners.add(fn); return () => listeners.delete(fn) }, () => model)
      // SDK index.ts:1696-1697,1741 exports host-styled primitives.
      const button = (label, onClick, disabled = false, variant = 'secondary') => h(Button,
        { type: 'button', onClick, disabled, variant, size: 'sm' }, label)
      const meta = { color: 'var(--ui-text-secondary)', fontSize: 13, lineHeight: 1.6, margin: 0 }
      const states = {
        'no-board': ['Open any session to load rulings for its profile', 'Then return to Rulings from the sidebar.'],
        empty: ['No rulings yet', 'Save a human answer with /ruling add in a session for this profile.'],
        unavailable: ['Unavailable', 'Check the gateway connection, then refresh.'],
      }
      return h('section', { style: { padding: 24, overflow: 'auto', height: '100%', color: 'var(--ui-text-primary)', fontFamily: 'inherit' }, 'aria-label': 'Rulings' },
        h('div', { style: { maxWidth: 960, margin: '0 auto' } },
          h('header', { style: { display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 16, justifyContent: 'space-between', marginBottom: 24 } },
            h('div', null,
              h('h1', { style: { fontSize: 24, fontWeight: 600, margin: '0 0 6px' } }, 'Rulings'),
              h('p', { style: meta }, view.board ? `Board ${view.board}. Completed-job citations and recorded vetoes.` : 'Focused profile and current board.')),
            button('Refresh', () => { void refresh() }, view.busy)),
          view.error ? h('p', { role: 'alert', style: { ...meta, color: 'var(--destructive)', marginBottom: 16 } }, view.error) : null,
          view.busy ? h('p', { role: 'status' }, 'Retiring; re-reading the store…')
            : view.state !== 'ready' ? h('div', { role: 'status' }, h(EmptyState, {
              title: states[view.state][0], description: states[view.state][1],
            })) : null,
          view.cap_reached ? h('p', { role: 'status', style: meta }, 'veto cap reached (recorded for a task on this board)') : null,
          view.truncated ? h('p', { style: meta }, `Showing ${view.rows.length} of ${view.total} ${plural(view.total, 'ruling')}. Text is limited to 2,000 characters; job lists to 20 IDs.`) : null,
          ...(view.rows || []).map(row => h('article', { key: row.id, style: { borderTop: '1px solid var(--ui-stroke-secondary)', padding: '20px 0', overflowWrap: 'anywhere', display: 'grid', gap: 12 } },
            h('div', { style: { display: 'flex', gap: 10, alignItems: 'baseline', flexWrap: 'wrap' } },
              h('h2', { style: { fontSize: 18, fontWeight: 500, lineHeight: 1.5, margin: 0, minWidth: 0, flex: '1 1 280px' } }, `${row.id} ${row.title}`),
              h(Badge, { variant: row.status === 'active' ? 'success' : 'muted' }, row.status)),
            h('div', { style: meta },
              h('p', { style: { margin: 0 } }, `keys: ${row.keys.join(', ') || '(none)'} · cited by ${row.cited_count} completed ${plural(row.cited_count, 'job')}`),
              h('p', { style: { margin: 0 } }, `${plural(row.veto_count, 'Veto', 'Vetoes')}: ${row.veto_count} · last veto: ${row.last_veto ? age(row.last_veto) : 'none'}`)),
            row.cap_reached ? h('p', { style: meta }, 'veto cap reached') : null,
            h('details', null, h('summary', { style: { cursor: 'pointer' } }, 'Ruling, receipt and timeline'),
              h('p', { style: { whiteSpace: 'pre-wrap', margin: '12px 0', lineHeight: 1.6 } }, row.ruling),
              h('p', { style: meta }, `Saved answer receipt: ${row.receipt.author || 'author not recorded'} · ${row.receipt.surface || 'source not recorded'} · ${when(row.receipt.at)}`),
              row.receipt.source_task ? h('p', { style: meta }, `Source card: ${row.receipt.source_task}`) : null,
              h('p', { style: meta }, 'Author is a recorded CLI user or slash session label, not an authenticated approver. The answer is shown above.'),
              h('h3', { style: { fontSize: 14, fontWeight: 500, margin: '16px 0 8px' } }, 'Timeline'),
              h('ol', { 'aria-label': `Timeline for ${row.id}`, style: { ...meta, paddingLeft: 20, display: 'grid', gap: 6 } },
                ...row.timeline.map((event, index) => h('li', { key: index },
                  event.at ? h('time', { dateTime: event.at }, when(event.at)) : 'time not recorded',
                  ` · ${event.kind}${event.task_id ? ` · card ${event.task_id}` : ''}${event.detail ? ` · ${event.detail}` : ''}`))),
              row.timeline_total > row.timeline.length ? h('p', { style: meta },
                `Showing ${row.timeline.length} of ${row.timeline_total} timeline events: saved, the latest 50 cite/explain records, and retirement when present.`) : null,
              h('p', { style: meta }, `Completed ${plural(row.cited_count, 'job')} (${row.jobs.length}/${row.cited_count} shown): ${row.jobs.join(', ') || '(none)'}`),
              h('p', { style: meta }, 'Question and ruling text limited to 2,000 characters; job list limited to 20 IDs.')),
            row.status === 'active' && view.confirm?.id !== row.id ? h('div', null, button(`Retire ${row.id}`, () => {
              if (model.state === 'ready') publish({ ...model, confirm: { id: row.id, board: view.board, key: scope() }, error: '' })
            }, view.busy, 'destructive')) : null,
            view.confirm?.id === row.id ? h('div', { role: 'group', 'aria-label': `Confirm retirement of ${row.id}`, style: { display: 'grid', gap: 12, padding: 16, background: 'var(--ui-bg-quaternary)', borderRadius: 4 } },
              h('p', { style: { margin: 0, lineHeight: 1.6 } }, `Retire ${row.id} on board ${view.board}? It will stop being offered to new workers. Existing jobs stay unchanged.`),
              h('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 8 } },
                button(`Confirm retire ${row.id}`, confirmRetire, view.busy, 'destructive'),
                button('Cancel', () => publish({ ...model, confirm: null }), view.busy))) : null))))
    }
    ctx.register({ id: 'rulings-page', title: 'Rulings', area: ROUTES_AREA, data: { path: PATH }, render: () => h(Page) })
    ctx.register({ id: 'rulings-nav', area: SIDEBAR_NAV_AREA, order: 55,
      data: { codicon: 'book', label: 'Rulings', path: PATH } })
    const changed = () => { generation += 1; clear(); void refresh() }
    for (const atom of [host.state.focusedSessionId, host.state.focusedSessionProfile, host.state.focusedSessionOwner, host.state.gateway]) {
      ctx.onDispose(atom.subscribe(changed))
    }
    ctx.onDispose(() => { disposed = true; generation += 1; clear(); listeners.clear() })
    ctx.setInterval(refresh, 3000)
    ctx.setInterval(() => {
      if ((lastSuccess !== null && Date.now() - lastSuccess >= 5000) || (pending && Date.now() - pending.started >= 5000)) clear()
    }, 1000)
    void refresh()
  },
}
