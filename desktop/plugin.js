import { host, STATUSBAR_AREAS } from '@hermes/plugin-sdk'

// Native data contribution: no renderer, dependencies, build, or persistent state.
export default {
  id: 'precedent-log',
  name: 'Precedent Log',
  register(ctx) {
    let disposeChip = () => {}
    let displayedLine = null
    let generation = 0
    let pending = null
    let disposed = false
    let lastSuccess = null
    const scope = () => JSON.stringify([
      host.state.focusedSessionId.get(),
      host.state.focusedSessionProfile.get(),
      host.state.gateway.get(),
      host.state.focusedSessionOwner.get(),
    ])
    const clear = () => { disposeChip(); disposeChip = () => {}; displayedLine = null; lastSuccess = null }
    const refresh = async () => {
      const key = scope()
      const session = host.state.focusedSessionId.get()
      const profile = host.state.focusedSessionProfile.get()
      const owner = host.state.focusedSessionOwner.get()
      if (!owner || owner.profile !== profile) { clear(); return }
      if (disposed || !session || host.state.gateway.get() !== 'open') { clear(); return }
      // Never accumulate uncancellable SDK operations across focus changes.
      if (pending) {
        if (Date.now() - pending.started >= 5000) clear()
        return
      }
      const ticket = { key, generation, started: Date.now() }
      pending = ticket
      try {
        const routes = await host.profileRoutes()
        if (disposed || ticket.generation !== generation || scope() !== key) return
        if (Date.now() - ticket.started >= 5000) { clear(); return }
        const route = routes.find(item =>
          item.connectionId === owner.connectionId && item.profile === owner.profile)
        if (!route) { clear(); return }
        const result = await host.requestProfile(route, 'slash.exec', {
          session_id: session, profile, command: '/rulings status',
        }, 2000)
        if (disposed || ticket.generation !== generation || scope() !== key) return
        if (Date.now() - ticket.started >= 5000) { clear(); return }
        const output = result?.type === 'exec' && typeof result.output === 'string'
          && result.output.length <= 256 ? result.output : ''
        const match = /^precedent-log status v1\nrulings=(0|[1-9][0-9]{0,8}); (?:no veto yet|veto=(P-[1-9][0-9]{0,8}); title=([^;\x00-\x1f\x7f-\x9f]{1,40}); at=([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z))$/u.exec(output)
        if (!match || match[0] !== output) { clear(); return }
        let last = 'no veto yet'
        if (match[2]) {
          const timestamp = Date.parse(match[4])
          if (!Number.isFinite(timestamp) || new Date(timestamp).toISOString().replace('.000Z', 'Z') !== match[4]
              || timestamp > Date.now()) { clear(); return }
          const seconds = Math.floor((Date.now() - timestamp) / 1000)
          const age = seconds < 60 ? 'just now' : seconds < 3600 ? `${Math.floor(seconds / 60)} min ago`
            : seconds < 86400 ? `${Math.floor(seconds / 3600)} hr ago` : `${Math.floor(seconds / 86400)} days ago`
          last = `last veto: ${match[2]} ${match[3]}, ${age}`
        }
        const line = `Precedent Log · ${match[1]} rulings · ${last}`
        lastSuccess = Date.now()
        if (line === displayedLine) return
        clear()
        disposeChip = ctx.register({
          id: 'precedent-status', area: STATUSBAR_AREAS.right, order: 130,
          data: {
            id: 'precedent-status', label: line,
            title: 'Counts active rulings and the latest recorded gate veto on the current board in the focused profile.',
          },
        })
        displayedLine = line
        lastSuccess = Date.now()
      } catch {
        if (!disposed && ticket.generation === generation && scope() === key) clear()
      } finally {
        if (pending === ticket) pending = null
        if (!disposed && ticket.generation !== generation) void refresh()
      }
    }
    const changed = () => { generation += 1; clear(); refresh() }
    for (const atom of [host.state.focusedSessionId, host.state.focusedSessionProfile, host.state.focusedSessionOwner, host.state.gateway]) {
      ctx.onDispose(atom.subscribe(changed))
    }
    ctx.onDispose(() => { disposed = true; generation += 1; clear() })
    ctx.setInterval(refresh, 3000)
    ctx.setInterval(() => {
      if ((lastSuccess !== null && Date.now() - lastSuccess >= 5000)
          || (pending && Date.now() - pending.started >= 5000)) clear()
    }, 1000)
    refresh()
  },
}
