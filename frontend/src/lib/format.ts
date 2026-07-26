export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("tr-TR", {
    style: "currency",
    currency: "TRY",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatCompact(value: number): string {
  return new Intl.NumberFormat("tr-TR", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

const DAY_LABEL = new Intl.DateTimeFormat("tr-TR", { day: "2-digit", month: "2-digit" });
const MONTH_LABEL = new Intl.DateTimeFormat("tr-TR", { month: "short", year: "2-digit" });

export interface DailyPoint {
  date: string;
  label: string;
  total: number;
  count: number;
}

/** Satış listesini son N gün için günlük toplam/adet serisine indirger (dashboard trend grafiği). */
export function groupByDay(
  items: { created_at: string; total_amount: number | string }[],
  days = 14
): DailyPoint[] {
  const buckets = new Map<string, DailyPoint>();
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    buckets.set(key, { date: key, label: DAY_LABEL.format(d), total: 0, count: 0 });
  }

  for (const item of items) {
    const key = item.created_at.slice(0, 10);
    const bucket = buckets.get(key);
    if (bucket) {
      bucket.total += Number(item.total_amount);
      bucket.count += 1;
    }
  }

  return Array.from(buckets.values());
}

export interface MonthlyFinancePoint {
  month: string;
  label: string;
  income: number;
  expense: number;
  net: number;
}

/** Finans işlemlerini son N ay için aylık gelir/gider/net serisine indirger. */
export function groupFinanceByMonth(
  items: { type: "income" | "expense"; amount: number | string; created_at: string }[],
  months = 6
): MonthlyFinancePoint[] {
  const buckets = new Map<string, MonthlyFinancePoint>();
  const now = new Date();

  for (let i = months - 1; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    buckets.set(key, { month: key, label: MONTH_LABEL.format(d), income: 0, expense: 0, net: 0 });
  }

  for (const item of items) {
    const d = new Date(item.created_at);
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    const bucket = buckets.get(key);
    if (!bucket) continue;
    const amount = Number(item.amount);
    if (item.type === "income") bucket.income += amount;
    else bucket.expense += amount;
    bucket.net = bucket.income - bucket.expense;
  }

  return Array.from(buckets.values());
}
