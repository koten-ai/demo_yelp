import type { ReactNode } from "react";

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

export function EmptyState({
  title,
  body,
  action,
}: {
  title: string;
  body?: string;
  /** Optional CTA under the body (e.g. Ask AI failover). */
  action?: ReactNode;
}) {
  return (
    <div className="text-center py-16 px-6">
      <span className="material-symbols-outlined text-4xl text-primary/40">search_off</span>
      <h3 className="mt-3 font-semibold text-on-surface">{title}</h3>
      {body && <p className="mt-1 text-sm text-on-surface-variant">{body}</p>}
      {action && <div className="mt-5 flex justify-center">{action}</div>}
    </div>
  );
}

export function LoadingBlock({ label = "Searching with Zeus…" }: { label?: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex flex-col items-center justify-center gap-2 py-12 text-primary"
    >
      <div className="flex items-center justify-center gap-3">
        <span className="material-symbols-outlined animate-spin">progress_activity</span>
        <span className="text-sm font-medium">{label}</span>
      </div>
    </div>
  );
}
