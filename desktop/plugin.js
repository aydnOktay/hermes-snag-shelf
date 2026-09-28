/**
 * Snag Shelf — everything that snagged, one full page.
 *
 * Unified package: copy to $HERMES_HOME/desktop-plugins/snag-shelf/.
 * Uses host.composer.insertText (Hermes >= 0.21.5) — never hermes:composer-insert.
 */

import {
  host,
  useQuery,
  useMutation,
  queryClient,
  ROUTES_AREA,
  SIDEBAR_NAV_AREA,
  STATUSBAR_AREAS,
} from '@hermes/plugin-sdk'
import { jsx, jsxs } from 'react/jsx-runtime'
import { useMemo, useState } from 'react'

const PAGE_PATH = '/snag-shelf'

let stylesInjected = false
function ensureStyles() {
  if (stylesInjected || typeof document === 'undefined') return
  stylesInjected = true
  const el = document.createElement('style')
  el.setAttribute('data-snag-shelf', '1')
  el.textContent = `
    @keyframes ss-fade-up {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .ss-page { animation: ss-fade-up 0.4s ease-out; }
    .ss-card { animation: ss-fade-up 0.35s ease-out both; }
    .ss-card:nth-child(1) { animation-delay: 0.03s; }
    .ss-card:nth-child(2) { animation-delay: 0.06s; }
    .ss-card:nth-child(3) { animation-delay: 0.09s; }
    .ss-btn:hover { filter: brightness(1.08); }
    .ss-btn:active { transform: translateY(1px); }
    .ss-btn:disabled { opacity: 0.45; cursor: wait; }
  `
  document.head.appendChild(el)
}

function useShelf(ctx, kind) {
  return useQuery({
    queryKey: ['snag-shelf', 'shelf', kind],
    queryFn: () => ctx.rest(`/shelf?kind=${encodeURIComponent(kind || 'all')}`),
    refetchInterval: 4000,
  })
}

function formatWhen(iso) {
  const s = (iso || '').replace('T', ' ')
  return s.length >= 19 ? s.slice(0, 19) : s
}

function btnStyle(kind) {
  const base = {
    fontSize: 12,
    padding: '7px 12px',
    borderRadius: 7,
    cursor: 'pointer',
    fontWeight: 500,
    letterSpacing: '0.01em',
    transition: 'filter 0.12s ease, transform 0.08s ease',
  }
  if (kind === 'primary') {
    return {
      ...base,
      color: 'var(--ui-text-on-accent, var(--ui-text-primary))',
      background: 'var(--ui-accent)',
      border: '1px solid transparent',
    }
  }
  return {
    ...base,
    color: 'var(--ui-text-secondary)',
    background: 'transparent',
    border: '1px solid var(--ui-stroke-secondary)',
  }
}

function chipStyle(active) {
  return {
    fontSize: 12,
    padding: '5px 10px',
    borderRadius: 999,
    cursor: 'pointer',
    border: '1px solid var(--ui-stroke-secondary)',
    color: active ? 'var(--ui-text-primary)' : 'var(--ui-text-tertiary)',
    background: active
      ? 'color-mix(in srgb, var(--ui-accent) 14%, transparent)'
      : 'transparent',
    fontWeight: active ? 600 : 400,
  }
}

function buildFixPrompt(item) {
  const tool = item.tool || '?'
  const kind = item.kind || 'other'
  const status = item.status || 'error'
  const args = item.args_summary || '(none)'
  const err = item.error || '(no message)'
  return (
    'Please fix this Hermes tool failure:\n\n' +
    `Tool: \`${tool}\` (${kind})\n` +
    `Status: ${status}\n` +
    `Args: ${args}\n` +
    `Error: ${err}\n\n` +
    'What went wrong and how should we recover?'
  )
}

async function insertText(text) {
  const trimmed = (text || '').trim()
  if (!trimmed) return
  // SDK composer verb (Hermes >= 0.21.5)
  if (
    host.composer &&
    typeof host.composer.insertText === 'function' &&
    (await host.composer.insertText(null, trimmed, { mode: 'block' }))
  ) {
    host.notify({ kind: 'info', message: 'Fix prompt inserted into the composer.' })
    return
  }
  if (host.os && typeof host.os.writeClipboard === 'function') {
    void host.os.writeClipboard(trimmed)
  }
  host.notify({
    kind: 'info',
    message: 'No open composer — prompt copied to the clipboard.',
  })
}

function ItemCard({ item, onPin, onRemove, busy }) {
  return jsxs('article', {
    className: 'ss-card',
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 10,
      padding: '16px 16px 14px',
      marginBottom: 10,
      borderRadius: 10,
      border: '1px solid var(--ui-stroke-secondary)',
      background:
        'linear-gradient(135deg, color-mix(in srgb, var(--ui-accent) 5%, transparent) 0%, transparent 40%)',
      boxShadow: item.pinned ? 'inset 3px 0 0 0 var(--ui-accent)' : 'none',
    },
    children: [
      jsxs('div', {
        style: { display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 8 },
        children: [
          jsx('span', {
            style: {
              fontWeight: 650,
              fontSize: 14,
              color: 'var(--ui-text-primary)',
              wordBreak: 'break-all',
            },
            children: item.tool || 'tool',
          }),
          jsx('span', {
            style: {
              fontSize: 10,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              padding: '2px 7px',
              borderRadius: 999,
              border: '1px solid var(--ui-stroke-secondary)',
              color: 'var(--ui-text-tertiary)',
            },
            children: item.kind || 'other',
          }),
          jsx('span', {
            style: {
              fontSize: 10,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
              padding: '2px 7px',
              borderRadius: 999,
              border: '1px solid var(--ui-stroke-secondary)',
              color: 'var(--ui-text-tertiary)',
            },
            children: item.status || 'error',
          }),
          item.pinned
            ? jsx('span', {
                style: {
                  fontSize: 10,
                  color: 'var(--ui-accent)',
                  fontWeight: 600,
                },
                children: 'pinned',
              })
            : null,
        ],
      }),
      jsx('div', {
        style: {
          fontSize: 11,
          color: 'var(--ui-text-tertiary)',
        },
        children: formatWhen(item.at),
      }),
      item.args_summary
        ? jsx('div', {
            style: {
              fontSize: 11,
              lineHeight: 1.45,
              color: 'var(--ui-text-quaternary, var(--ui-text-tertiary))',
              wordBreak: 'break-word',
              fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
            },
            children: item.args_summary,
          })
        : null,
      item.error
        ? jsx('div', {
            style: {
              fontSize: 13,
              lineHeight: 1.5,
              color: 'var(--ui-text-secondary)',
              wordBreak: 'break-word',
            },
            children: item.error,
          })
        : null,
      jsxs('div', {
        style: { display: 'flex', flexWrap: 'wrap', gap: 8 },
        children: [
          jsx('button', {
            type: 'button',
            className: 'ss-btn',
            onClick: () => insertText(buildFixPrompt(item)),
            style: btnStyle('primary'),
            children: 'Insert fix prompt',
          }),
          jsx('button', {
            type: 'button',
            className: 'ss-btn',
            onClick: () => insertText(item.error || ''),
            style: btnStyle('quiet'),
            children: 'Insert error',
          }),
          jsx('button', {
            type: 'button',
            className: 'ss-btn',
            disabled: busy,
            onClick: () => onPin(item),
            style: btnStyle('quiet'),
            children: item.pinned ? 'Unpin' : 'Pin',
          }),
          jsx('button', {
            type: 'button',
            className: 'ss-btn',
            disabled: busy,
            onClick: () => onRemove(item),
            style: { ...btnStyle('quiet'), opacity: 0.8 },
            children: 'Remove',
          }),
        ],
      }),
    ],
  })
}

function ShelfPage({ ctx }) {
  ensureStyles()
  const [kind, setKind] = useState('all')
  const query = useShelf(ctx, kind)
  const items = (query.data && query.data.items) || []
  const ordered = useMemo(() => {
    const pinned = items.filter((it) => it.pinned)
    const rest = items.filter((it) => !it.pinned)
    return [...pinned.reverse(), ...rest.reverse()]
  }, [items])

  const pinMut = useMutation({
    mutationFn: (body) => ctx.rest('/pin', { method: 'POST', body }),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['snag-shelf'] }),
  })
  const removeMut = useMutation({
    mutationFn: (body) => ctx.rest('/remove', { method: 'POST', body }),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['snag-shelf'] }),
  })
  const clearMut = useMutation({
    mutationFn: () => ctx.rest('/clear', { method: 'POST', body: { keep_pinned: true } }),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['snag-shelf'] }),
  })

  const busy = pinMut.isPending || removeMut.isPending

  return jsxs('div', {
    className: 'ss-page',
    style: {
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      overflow: 'auto',
      padding: '36px 40px 64px',
      maxWidth: 780,
      margin: '0 auto',
      color: 'var(--ui-text-secondary)',
      boxSizing: 'border-box',
    },
    children: [
      jsxs('header', {
        children: [
          jsx('div', {
            style: {
              fontSize: 11,
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
              color: 'var(--ui-text-tertiary)',
              fontWeight: 600,
              marginBottom: 12,
            },
            children: 'Snag Shelf',
          }),
          jsx('h1', {
            style: {
              margin: 0,
              fontSize: 'clamp(28px, 4vw, 36px)',
              fontWeight: 700,
              lineHeight: 1.15,
              letterSpacing: '-0.02em',
              color: 'var(--ui-text-primary)',
            },
            children: 'Everything that snagged.',
          }),
          jsx('p', {
            style: {
              margin: '12px 0 0',
              fontSize: 14,
              lineHeight: 1.55,
              maxWidth: 520,
              color: 'var(--ui-text-secondary)',
            },
            children:
              'Cross-session shelf of failed tool calls — pin keepers, insert a fix prompt, clear the rest.',
          }),
        ],
      }),
      jsxs('div', {
        style: {
          display: 'flex',
          flexWrap: 'wrap',
          gap: 8,
          marginTop: 22,
          alignItems: 'center',
        },
        children: [
          ...['all', 'terminal', 'file', 'web', 'other'].map((k) =>
            jsx(
              'button',
              {
                type: 'button',
                onClick: () => setKind(k),
                style: chipStyle(kind === k),
                children: k,
              },
              k,
            ),
          ),
          jsx('div', { style: { flex: 1 } }),
          jsx('div', {
            style: { fontSize: 12, color: 'var(--ui-text-tertiary)' },
            children: `${ordered.length} snags`,
          }),
          ordered.length
            ? jsx('button', {
                type: 'button',
                className: 'ss-btn',
                disabled: clearMut.isPending,
                onClick: () => clearMut.mutate(),
                style: btnStyle('quiet'),
                children: 'Clear unpinned',
              })
            : null,
        ],
      }),
      ordered.length
        ? jsx('div', {
            style: { marginTop: 18 },
            children: ordered.map((item) =>
              jsx(
                ItemCard,
                {
                  item,
                  busy,
                  onPin: (it) => pinMut.mutate({ id: it.id, pinned: !it.pinned }),
                  onRemove: (it) => removeMut.mutate({ id: it.id }),
                },
                item.id,
              ),
            ),
          })
        : jsxs('div', {
            style: {
              marginTop: 28,
              padding: '36px 28px',
              borderRadius: 12,
              border: '1px dashed var(--ui-stroke-secondary)',
              background:
                'radial-gradient(ellipse at 20% 0%, color-mix(in srgb, var(--ui-accent) 10%, transparent), transparent 55%)',
            },
            children: [
              jsx('div', {
                style: {
                  fontSize: 12,
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  color: 'var(--ui-text-tertiary)',
                  marginBottom: 10,
                },
                children: 'Empty shelf',
              }),
              jsx('div', {
                style: {
                  fontSize: 17,
                  fontWeight: 600,
                  color: 'var(--ui-text-primary)',
                  marginBottom: 8,
                },
                children: 'No snags yet.',
              }),
              jsx('div', {
                style: {
                  fontSize: 13,
                  lineHeight: 1.55,
                  color: 'var(--ui-text-secondary)',
                  maxWidth: 440,
                },
                children:
                  'When a Hermes tool fails, blocks, or times out, it lands here — across sessions.',
              }),
            ],
          }),
    ],
  })
}

function StatusChip({ ctx }) {
  ensureStyles()
  const query = useShelf(ctx, 'all')
  const count = (query.data && query.data.count) || 0
  const label = count ? `snags ${count}` : 'snags'
  return jsx('button', {
    type: 'button',
    title: 'Open Snag Shelf',
    onClick: () => host.navigate(PAGE_PATH),
    style: {
      fontSize: 11,
      padding: '3px 9px',
      borderRadius: 999,
      border: '1px solid var(--ui-stroke-secondary)',
      background: count
        ? 'color-mix(in srgb, var(--ui-accent) 12%, transparent)'
        : 'transparent',
      color: count ? 'var(--ui-text-primary)' : 'var(--ui-text-tertiary)',
      cursor: 'pointer',
      fontWeight: count ? 650 : 400,
    },
    children: label,
  })
}

export default {
  id: 'snag-shelf',
  name: 'Snag Shelf',
  defaultEnabled: true,
  register(ctx) {
    ctx.registerMany([
      {
        id: 'page',
        area: ROUTES_AREA,
        data: { path: PAGE_PATH },
        render: () => jsx(ShelfPage, { ctx }),
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        order: 47,
        data: { path: PAGE_PATH, label: 'Snag Shelf', codicon: 'warning' },
      },
      {
        id: 'chip',
        area: STATUSBAR_AREAS.right,
        order: 88,
        render: () => jsx(StatusChip, { ctx }),
      },
    ])
  },
}
