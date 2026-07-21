type Props = { message: string; onDismiss?: () => void };

export function ErrorBanner({ message, onDismiss }: Props) {
  if (!message) return null;
  return (
    <div
      role="alert"
      className="rounded-xl bg-error-container text-error px-4 py-3 flex items-start justify-between gap-3"
    >
      <div className="flex gap-2 items-start">
        <span className="material-symbols-outlined">error</span>
        <p className="text-sm">{message}</p>
      </div>
      {onDismiss && (
        <button type="button" onClick={onDismiss} className="text-sm underline">
          Dismiss
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title, body }: { title: string; body?: string }) {
  return (
    <div className="text-center py-16 px-6">
      <span className="material-symbols-outlined text-4xl text-primary/40">search_off</span>
      <h3 className="mt-3 font-semibold text-on-surface">{title}</h3>
      {body && <p className="mt-1 text-sm text-on-surface-variant">{body}</p>}
    </div>
  );
}

export function LoadingBlock({ label = "Searching with Zeus…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-12 text-primary">
      <span className="material-symbols-outlined animate-spin">progress_activity</span>
      <span className="text-sm font-medium">{label}</span>
    </div>
  );
}
