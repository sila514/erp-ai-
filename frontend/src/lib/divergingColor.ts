/**
 * Diverging (kutupsal) renk ölçeği — SADECE işaretli büyüklükler için (korelasyon,
 * fark). Kategorik `series.*` renklerinden bilinçli olarak ayrı (bkz.
 * tailwind.config.js `diverging`). r=0 nötr griye, |r|=1 tam doygun uca gider.
 */
const POSITIVE = { r: 0x39, g: 0x87, b: 0xe5 }; // tailwind: diverging.positive
const NEGATIVE = { r: 0xe6, g: 0x67, b: 0x67 }; // tailwind: diverging.negative
const NEUTRAL = { r: 0x33, g: 0x41, b: 0x55 }; // tailwind: diverging.neutral

function lerp(a: number, b: number, t: number): number {
  return Math.round(a + (b - a) * t);
}

export function correlationColor(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "rgba(148, 163, 184, 0.12)";
  }
  const t = Math.min(Math.abs(value), 1);
  const target = value >= 0 ? POSITIVE : NEGATIVE;
  const r = lerp(NEUTRAL.r, target.r, t);
  const g = lerp(NEUTRAL.g, target.g, t);
  const b = lerp(NEUTRAL.b, target.b, t);
  return `rgb(${r}, ${g}, ${b})`;
}

export function correlationTextColor(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "rgba(148,163,184,0.5)";
  return Math.abs(value) > 0.55 ? "#f8fafc" : "rgba(226,232,240,0.75)";
}
