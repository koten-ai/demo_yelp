import { useCallback, type ComponentProps } from "react";
import { Link, NavLink, useLocation, useNavigate, type NavigateOptions } from "react-router-dom";

/** Truthy debug values that keep the chat-trace inspector on SPA navigations. */
const TRUTHY_DEBUG = new Set(["1", "true", "yes", "on"]);

/** Raw `debug` query when it is 1, true, yes, or on. Otherwise null. */
export function debugQueryValue(search: string): string | null {
  const raw = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search).get(
    "debug"
  );
  if (raw == null) return null;
  if (!TRUTHY_DEBUG.has(raw.trim().toLowerCase())) return null;
  return raw;
}

/**
 * Keep a truthy debug query on /, /search, /chat, and /business/:id.
 * Other query keys already on `path` stay. A falsey debug value is dropped.
 */
export function withDebugQuery(path: string, search: string): string {
  const debug = debugQueryValue(search);
  const hashAt = path.indexOf("#");
  const hash = hashAt >= 0 ? path.slice(hashAt) : "";
  const before = hashAt >= 0 ? path.slice(0, hashAt) : path;
  const queryAt = before.indexOf("?");
  const pathname = queryAt >= 0 ? before.slice(0, queryAt) : before;
  const params = new URLSearchParams(queryAt >= 0 ? before.slice(queryAt + 1) : "");
  if (!debug) {
    params.delete("debug");
    const qs = params.toString();
    return `${pathname}${qs ? `?${qs}` : ""}${hash}`;
  }
  params.set("debug", debug);
  const qs = params.toString();
  return `${pathname}?${qs}${hash}`;
}

/** Navigate while keeping a truthy debug query on the next path. */
export function useDebugNavigate() {
  const nav = useNavigate();
  const { search } = useLocation();
  return useCallback(
    (path: string, options?: NavigateOptions) => nav(withDebugQuery(path, search), options),
    [nav, search]
  );
}

/** Link that keeps a truthy debug query. Non-string `to` is left unchanged. */
export function DebugLink({ to, ...rest }: ComponentProps<typeof Link>) {
  const { search } = useLocation();
  const href = typeof to === "string" ? withDebugQuery(to, search) : to;
  return <Link to={href} {...rest} />;
}

/** NavLink that keeps a truthy debug query. Non-string `to` is left unchanged. */
export function DebugNavLink({ to, ...rest }: ComponentProps<typeof NavLink>) {
  const { search } = useLocation();
  const href = typeof to === "string" ? withDebugQuery(to, search) : to;
  return <NavLink to={href} {...rest} />;
}
