/**
 * Resolves the URL the browser should use to connect to LiveKit's signaling
 * WebSocket, proxied through nginx at /livekit/ rather than hitting port
 * 7880 directly. Camera/mic access requires a secure context (https, or the
 * literal host "localhost"), so the app is served over https even on a bare
 * LAN IP; a page loaded over https can't open a plain ws:// connection to a
 * different port without the browser blocking it as mixed content, and
 * LiveKit's own server has no TLS listener of its own. Routing it through
 * nginx's existing TLS termination on the same origin sidesteps both.
 *
 * The backend returns its own configured LIVEKIT_URL in join responses, but
 * that setting reflects the *server's* view of itself, not the hostname the
 * browser actually used to reach the app - so we derive it from the page's
 * own origin instead, unless explicitly overridden.
 */
export function resolveLiveKitUrl(): string {
  if (process.env.NEXT_PUBLIC_LIVEKIT_URL) return process.env.NEXT_PUBLIC_LIVEKIT_URL;
  if (typeof window === "undefined") return "ws://localhost/livekit";
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/livekit`;
}
