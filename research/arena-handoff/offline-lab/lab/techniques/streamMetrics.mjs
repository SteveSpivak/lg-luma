// Lab metrics core — percentile/summary statistics for every measurement run in this lab
// (built 2026-10-27 for the YouTube ad-block/efficiency packet: every comparison must report
// p50/p90/p95 the same way, computed by ONE audited implementation, not per-script ad-hoc math).
//
// Convention: nearest-rank percentiles (sorted[ceil(p/100 * n) - 1]) — the conservative,
// order-statistics definition (no interpolation). For n=1 every percentile is the sample.

/** Nearest-rank percentile of a numeric array. p in (0, 100]. Empty array -> null. */
export function percentile(samples, p) {
  if (!Array.isArray(samples) || samples.length === 0) return null;
  if (!Number.isFinite(p) || p <= 0 || p > 100) throw new Error(`percentile p must be in (0, 100], got ${p}`);
  const sorted = [...samples].sort((a, b) => a - b);
  const rank = Math.max(1, Math.ceil((p / 100) * sorted.length));
  return sorted[rank - 1];
}

export function mean(samples) {
  if (!Array.isArray(samples) || samples.length === 0) return null;
  let total = 0;
  for (const s of samples) total += Number(s);
  return total / samples.length;
}

/** Population standard deviation (measurements here are complete populations per run). */
export function stdev(samples) {
  if (!Array.isArray(samples) || samples.length < 2) return null;
  const m = mean(samples);
  let acc = 0;
  for (const s of samples) acc += (Number(s) - m) ** 2;
  return Math.sqrt(acc / samples.length);
}

/**
 * The lab's standard summary line. Every A/B comparison in this packet reports these fields
 * for fps, startup ms, stall seconds, buffer occupancy, etc.
 */
export function summarize(samples, { label = "" } = {}) {
  if (!Array.isArray(samples) || samples.length === 0) {
    return { label, count: 0, min: null, max: null, mean: null, stdev: null, p50: null, p90: null, p95: null, p99: null };
  }
  const numeric = samples.map(Number).filter((v) => Number.isFinite(v));
  if (numeric.length === 0) throw new Error("summarize: no numeric samples");
  return {
    label,
    count: numeric.length,
    min: Math.min(...numeric),
    max: Math.max(...numeric),
    mean: mean(numeric),
    stdev: stdev(numeric),
    p50: percentile(numeric, 50),
    p90: percentile(numeric, 90),
    p95: percentile(numeric, 95),
    p99: percentile(numeric, 99),
  };
}

/** Format a summary as the one-line receipt string used across lab receipts. */
export function summaryLine(summary) {
  if (!summary || summary.count === 0) return `${summary?.label ?? ""}: no samples`;
  const f = (v) => (v == null ? "—" : Number(v).toFixed(1));
  return (
    `${summary.label || "samples"}: n=${summary.count} min=${f(summary.min)} p50=${f(summary.p50)} ` +
    `p90=${f(summary.p90)} p95=${f(summary.p95)} p99=${f(summary.p99)} max=${f(summary.max)} mean=${f(summary.mean)}`
  );
}

/**
 * Comparison verdict for A/B runs: a difference is REPORTED as a delta, but only called
 * SIGNIFICANT when the p95s do not overlap in the direction of the delta (a deliberately
 * conservative, falsification-first rule — better to under-claim than to over-claim).
 */
export function compareSummaries(a, b) {
  if (!a || !b || a.count === 0 || b.count === 0) return { deltaP50: null, significant: null };
  const deltaP50 = a.p50 - b.p50;
  let significant = null;
  if (deltaP50 > 0) significant = a.p90 > b.p50 && b.p95 < a.p50 ? true : a.p90 > b.p95 ? false : null;
  if (deltaP50 < 0) significant = b.p90 > a.p50 && a.p95 < b.p50 ? true : b.p90 > a.p95 ? false : null;
  return { deltaP50, significant };
}
