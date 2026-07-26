/**
 * Grafik renkleri - tailwind.config.js'teki `series`/`status` ile birebir aynı
 * (recharts ham hex bekler, Tailwind class'ı kullanamaz). Kategorik seriler
 * SABİT sırayla atanmalı (validate_palette.js ile doğrulandı, bkz. dataviz skill).
 */
export const SERIES = {
  blue: "#3987e5",
  orange: "#d95926",
  aqua: "#199e70",
  amber: "#c98500",
  magenta: "#d55181",
} as const;

export const SERIES_ORDER = [SERIES.blue, SERIES.orange, SERIES.aqua, SERIES.amber, SERIES.magenta];

export const STATUS = {
  good: "#0ca30c",
  warning: "#fab219",
  serious: "#ec835a",
  critical: "#d03b3b",
} as const;

export const CHART_GRID = "rgba(0,180,255,0.06)";
export const CHART_TICK = "rgba(130,200,255,0.45)";
