const PALETTE = ["#1d1d1f", "#3a3a3d", "#56565b", "#75757a", "#8d8d92", "#a4a4a9"];

export function stableColor(seed: string): string {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = (hash << 5) - hash + seed.charCodeAt(i);
    hash |= 0;
  }
  return PALETTE[Math.abs(hash) % PALETTE.length];
}
