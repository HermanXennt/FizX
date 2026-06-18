function defaultWsBaseUrl(): string {
  if (typeof window === "undefined") return "ws://localhost";
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}`;
}

// Same reasoning as API_BASE_URL: derive from the page's own origin so one
// build works whether it's loaded via localhost, a LAN IP, or a real domain.
export const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || defaultWsBaseUrl();

export function buildSocketUrl(path: string, token: string | null): string {
  const url = new URL(`${WS_BASE_URL}${path}`);
  if (token) url.searchParams.set("token", token);
  return url.toString();
}
