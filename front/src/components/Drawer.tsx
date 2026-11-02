import { useEffect, useRef } from 'react'
import type { ReactNode } from 'react'


export default function Drawer({ title, children, busy = false, onClose }: {
  title: string; children: ReactNode; busy?: boolean; onClose: () => void
}) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const dialog = ref.current
    const previous = document.activeElement
    if (dialog && !dialog.open) dialog.showModal()
    return () => {
      dialog?.close()
      if (previous instanceof HTMLElement) previous.focus()
    }
  }, [])
  return <dialog ref={ref} className="drawer" aria-label={title}
    onCancel={event => { event.preventDefault(); if (!busy) onClose() }}>
    <header className="drawer-header"><h2>{title}</h2><button type="button" className="secondary-button" aria-label="Fechar formulário" disabled={busy} onClick={onClose}>✕</button></header>
    <div className="drawer-content">{children}</div>
  </dialog>
}
