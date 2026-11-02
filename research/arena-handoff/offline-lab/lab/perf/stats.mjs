// Experiment statistics engine (Assignment 05, Tasks A + C). PURE — no CDP, no fs, no clock.
// One audited implementation of every number the experiment system prints.
//
// METRIC SEMANTICS (Task A — binding, see lab/perf/EXPERIMENT-CLI.md §2):
//   frameIntervalMs.*        nearest-rank percentiles of frame intervals (the primary metric)
//   fpsImpliedByPercentileInterval.*  1000 / percentile(frame interval) — an INVERSION of an
//                            order statistic. It is NOT a percentile of FPS samples and must
//                            never be labelled "p95 fps". Lower is worse, same tail as the gap.
//   instantaneousFps.*       nearest-rank percentiles of per-frame 1000/gap samples (p05 = the
//                            worst-5% frame speed — the meaningful low tail)
//   meanFpsOverElapsed       gap count / elapsed gap time (throughput, not a percentile)
//   refreshEstimate          display cadence estimated from the mode of the fastest half of
//                            gaps, snapped to standard rates — an ESTIMATE, always labelled
//   droppedFrames            gaps >= 2x the estimated refresh period — an ESTIMATE
//   longTasks                PerformanceObserver longtask durations (ms)
//   layers.*.textureEstimateMB  computed: sum(layer pixels) * 4B — an ESTIMATE, not a readout
//   metrics.JSHeapUsedSize   measured V8 JS heap — NOT process memory, NOT GPU memory
//
// INDEPENDENCE (Task C): frames within a run are autocorrelated and are NEVER treated as
// independent replicates. Inference (CI, effect size, verdict) uses run-level and pair-level
// values only. Initial protocol: four A/B/B/A cycles (8 pairs); more cycles follow observed
// variability and the predefined worthwhile effect — four pairs alone never yield a universal
// significance claim.
import { percentile, mean } from "../techniques/streamMetrics.mjs";

export { percentile as nearestRank };

const round1 = (x) => (typeof x === "number" && Number.isFinite(x) ? Math.round(x * 10) / 10 : null);
const countOver = (values, limit) => values.filter((x) => x > limit).length;

export const STANDARD_REFRESH_RATES = [24, 30, 50, 60, 75, 90, 120];

/**
 * Full frame statistics with corrected semantics (Task A). Accepts raw rAF gap samples;
 * filters nothing silently — every rejected sample is counted in clockAnomalies.
 */
export function frameStats(gapsMs, { standardRates = STANDARD_REFRESH_RATES } = {}) {
  const raw = Array.isArray(gapsMs) ? gapsMs : [];
  const finite = raw.filter((x) => typeof x === "number" && Number.isFinite(x));
  const clean = finite.filter((x) => x > 0 && x <= 60000);
  const anomalies = {
    nonFinite: raw.length - finite.length,
    nonPositive: finite.filter((x) => x <= 0).length,
    over60s: finite.filter((x) => x > 60000).length
  };
  const blockers = [];
  if (anomalies.nonPositive > 0 || anomalies.over60s > 0) blockers.push("frame-clock-anomaly");
  if (anomalies.nonFinite > 0) blockers.push("malformed-frame-samples"); // rejected, never silently coerced
  if (!clean.length) {
    blockers.push("no-valid-frame-samples");
    return {
      schema: "frame-stats/2",
      n: 0,
      nRaw: raw.length,
      frameIntervalMs: null,
      fpsImpliedByPercentileInterval: null,
      instantaneousFps: null,
      meanFpsOverElapsed: null,
      refreshEstimate: null,
      droppedFrames: null,
      longFrames: null,
      clockAnomalies: anomalies,
      blockers,
      note: "no valid frame samples — INCONCLUSIVE by construction, never a PASS"
    };
  }
  const sorted = [...clean].sort((a, b) => a - b);
  // Refresh estimate: mode (0.5 ms bins) of the fastest half of gaps — the vsync period when
  // most frames hit the display cadence. Snapped to standard rates within 8%; estimate:true.
  const fastHalf = sorted.slice(0, Math.ceil(sorted.length / 2));
  const bins = new Map();
  for (const g of fastHalf) {
    const b = Math.round(g * 2) / 2;
    bins.set(b, (bins.get(b) || 0) + 1);
  }
  const modeGap = [...bins.entries()].sort((a, b) => b[1] - a[1] || a[0] - b[0])[0][0];
  const rawHz = 1000 / modeGap;
  const snapped = standardRates.find((r) => Math.abs(r - rawHz) / r < 0.08);
  const refreshHz = snapped ?? Math.round(rawHz * 10) / 10;
  const periodMs = 1000 / refreshHz;
  const fpsSamples = clean.map((g) => 1000 / g);
  const totalMs = clean.reduce((a, b) => a + b, 0);
  const p = (q) => percentile(clean, q);
  return {
    schema: "frame-stats/2",
    n: clean.length,
    nRaw: raw.length,
    frameIntervalMs: { median: p(50), p90: p(90), p95: p(95), p99: p(99), max: sorted[sorted.length - 1] },
    // Inversions of interval percentiles — NOT percentiles of FPS samples (Task A):
    fpsImpliedByPercentileInterval: {
      fromMedian: round1(1000 / p(50)),
      fromP90: round1(1000 / p(90)),
      fromP95: round1(1000 / p(95)),
      note: "1000 / percentile(frame interval) — an interval inversion, not an FPS percentile"
    },
    // Percentiles of per-frame FPS samples — the low tail is what users feel:
    instantaneousFps: { p05: round1(percentile(fpsSamples, 5)), p50: round1(percentile(fpsSamples, 50)), min: round1(sorted[sorted.length - 1] ? 1000 / sorted[sorted.length - 1] : null) },
    meanFpsOverElapsed: round1((1000 * clean.length) / totalMs),
    refreshEstimate: { hz: refreshHz, method: "mode-of-fastest-half-gaps", modeGapMs: modeGap, estimate: true },
    droppedFrames: { count: clean.filter((g) => g >= 2 * periodMs).length, rule: "gap >= 2x estimated refresh period", estimate: true },
    longFrames: { over20ms: countOver(clean, 20), over33ms: countOver(clean, 33.4), over50ms: countOver(clean, 50), over100ms: countOver(clean, 100) },
    clockAnomalies: anomalies,
    blockers
  };
}

/** Back-compat wrapper (ghui.mjs v1 field names) — deprecated, do not use in new code. */
export function fpsFromGaps(gapsMs) {
  const f = frameStats(gapsMs);
  if (!f.frameIntervalMs) return { n: 0, gapMs: null, fps: null, avgFps: null };
  return {
    n: f.n,
    gapMs: { p50: f.frameIntervalMs.median, p90: f.frameIntervalMs.p90, p95: f.frameIntervalMs.p95, max: f.frameIntervalMs.max },
    fps: { p50: f.fpsImpliedByPercentileInterval.fromMedian, p90: f.fpsImpliedByPercentileInterval.fromP90, p95: f.fpsImpliedByPercentileInterval.fromP95 },
    avgFps: f.meanFpsOverElapsed
  };
}

// ---- inference on INDEPENDENT units only (runs / pairs) ----

/** Student-t two-sided 95% CI of the mean. n >= 2; returns null otherwise. Table pinned (df 1..30). */
const T95 = [12.7062, 4.3027, 3.1824, 2.7764, 2.5706, 2.4469, 2.3646, 2.306, 2.2622, 2.2281, 2.201, 2.1788, 2.1604, 2.1448, 2.1315, 2.1199, 2.1098, 2.1009, 2.093, 2.086, 2.0796, 2.0739, 2.0687, 2.0639, 2.0595, 2.0555, 2.0518, 2.0484, 2.0452, 2.0423];
export function tCi95(values) {
  const v = (values || []).filter((x) => typeof x === "number" && Number.isFinite(x));
  const n = v.length;
  if (n < 2) return { n, mean: n ? v[0] : null, ci: null, reason: n ? "single-sample-no-ci" : "no-samples" };
  const m = v.reduce((a, b) => a + b, 0) / n;
  const s = Math.sqrt(v.reduce((a, x) => a + (x - m) ** 2, 0) / (n - 1));
  if (s === 0) return { n, mean: m, ci: [m, m], zeroVariance: true };
  const t = n - 2 < T95.length ? T95[n - 2] : 1.96;
  const half = (t * s) / Math.sqrt(n);
  return { n, mean: m, ci: [m - half, m + half] };
}

/** Cohen's d for paired deltas (d_z). Zero variance -> null + flag (never a fabricated d). */
export function cohensD(values) {
  const v = (values || []).filter((x) => typeof x === "number" && Number.isFinite(x));
  if (v.length < 2) return { n: v.length, d: null, reason: "n<2" };
  const m = v.reduce((a, b) => a + b, 0) / v.length;
  const s = Math.sqrt(v.reduce((a, x) => a + (x - m) ** 2, 0) / (v.length - 1));
  if (s === 0) return { n: v.length, d: null, zeroVariance: true, note: "identical deltas — check the instrument, do not report d" };
  return { n: v.length, d: Math.round((m / s) * 1000) / 1000 };
}

/**
 * MAD-based outlier visibility (modified z-score > 3.5). Outliers are FLAGGED, never deleted.
 * MAD fallback: mean absolute deviation from the median when MAD === 0 (deterministic).
 */
export function madOutliers(values, { threshold = 3.5 } = {}) {
  const v = (values || []).filter((x) => typeof x === "number" && Number.isFinite(x));
  if (!v.length) return { n: 0, median: null, mad: null, outliers: [] };
  const sorted = [...v].sort((a, b) => a - b);
  const med = percentile(v, 50);
  const absDev = sorted.map((x) => Math.abs(x - med)).sort((a, b) => a - b);
  const mad = percentile(absDev, 50);
  const sigma = mad || mean(absDev) || 0;
  const outliers = [];
  if (sigma > 0) {
    for (let i = 0; i < v.length; i++) {
      const z = (0.6745 * (v[i] - med)) / sigma;
      if (Math.abs(z) > threshold) outliers.push({ index: i, value: v[i], modifiedZ: Math.round(z * 100) / 100 });
    }
  }
  return { n: v.length, median: med, mad, madFallbackUsed: mad === 0, outliers };
}

/** Within-arm order/drift check: split-half medians compared against the regression threshold. */
export function driftCheck(valuesInRunOrder, { threshold } = {}) {
  const v = (valuesInRunOrder || []).filter((x) => typeof x === "number" && Number.isFinite(x));
  if (v.length < 4) return { n: v.length, firstHalfMedian: null, secondHalfMedian: null, driftMagnitude: null, suspected: false, reason: "n<4-no-drift-test" };
  const half = Math.floor(v.length / 2);
  const h1 = percentile(v.slice(0, half), 50);
  const h2 = percentile(v.slice(v.length - half), 50);
  const magnitude = Math.abs(h2 - h1);
  const suspected = threshold != null && magnitude >= threshold;
  return { n: v.length, firstHalfMedian: h1, secondHalfMedian: h2, driftMagnitude: Math.round(magnitude * 100) / 100, suspected, rule: "split-half medians differ by >= regression threshold" };
}

/**
 * Pair an A/B/B/A design. Each cycle contributes two adjacent pairs: (pos1 A, pos2 B) and
 * (pos3 B, pos4 A). Delta is always candidate − baseline. Returns pairs or a validation error.
 */
export function pairAbba(runs, { baseline, candidate }) {
  const measured = (runs || []).filter((r) => r && r.role !== "warmup" && r.verdict === "MEASURED");
  const byCycle = new Map();
  for (const r of measured) {
    const k = r.cycle;
    if (!byCycle.has(k)) byCycle.set(k, []);
    byCycle.get(k).push(r);
  }
  const pairs = [];
  for (const k of [...byCycle.keys()].sort((a, b) => a - b)) {
    const cycleRuns = byCycle.get(k).slice().sort((a, b) => a.position - b.position);
    if (cycleRuns.length !== 4) return { error: `cycle ${k}: expected 4 measured runs, got ${cycleRuns.length}` };
    const labels = cycleRuns.map((r) => r.arm);
    const expected = [baseline, candidate, candidate, baseline];
    if (labels.join(",") !== expected.join(","))
      return { error: `cycle ${k}: arm order ${labels.join(",")} != A/B/B/A (${expected.join(",")})` };
    pairs.push({ cycle: k, baselineRun: cycleRuns[0], candidateRun: cycleRuns[1], adjacency: "A-then-B" });
    pairs.push({ cycle: k, baselineRun: cycleRuns[3], candidateRun: cycleRuns[2], adjacency: "B-then-A" });
  }
  return { pairs, cycles: byCycle.size };
}

/** Sample-size guidance from observed paired-delta SD and the predefined worthwhile effect. */
export function sampleSizeGuidance({ sdDelta, worthwhileDelta, currentPairs }) {
  if (!(sdDelta > 0) || !(worthwhileDelta > 0))
    return { sdDelta: sdDelta ?? null, worthwhileDelta: worthwhileDelta ?? null, requiredPairs: null, currentPairs: currentPairs ?? 0, note: "guidance unavailable (zero variance or missing worthwhile effect)" };
  const required = Math.ceil((((1.96 + 0.8416) * sdDelta) / worthwhileDelta) ** 2);
  return {
    sdDelta: Math.round(sdDelta * 100) / 100,
    worthwhileDelta,
    requiredPairs: required,
    currentPairs: currentPairs ?? 0,
    note: "planning hint (two-sided 95%, 80% power, paired) — not a gate; extend cycles when required > current"
  };
}

const pick = (obj, path) => String(path).split(".").reduce((o, k) => (o == null ? undefined : o[k]), obj);

/**
 * Compare arms on declared metrics. Pure. Verdict rules (documented, falsification-first):
 *   REGRESSED   medianDelta >= regressionThreshold AND all pairs same sign AND CI excludes 0
 *   IMPROVED    medianDelta <= -improvementThreshold AND all same sign AND CI excludes 0 (below 0)
 *   NO_CHANGE   CI entirely inside (-regressionThreshold, +regressionThreshold)
 *   INCONCLUSIVE anything else — including insufficient pairs, blockers, drift, missing data.
 * With n=4 pairs the claim is labelled "indicative", never a universal significance claim.
 */
export function compareMetrics(runs, { metrics, baseline, candidate, minPairs = 4 }) {
  const problems = [];
  const perMetric = {};
  let overall = "NO_CHANGE";
  const pairing = pairAbba(runs, { baseline, candidate });
  if (pairing.error) return { verdict: "INCONCLUSIVE", reason: pairing.error, blockers: ["invalid-pairing"], perMetric: {} };
  const pairs = pairing.pairs;
  for (const spec of metrics || []) {
    const path = spec.path;
    const label = spec.label || path;
    const deltas = [];
    const samples = { baseline: [], candidate: [] };
    let missing = 0;
    for (const pr of pairs) {
      const a = pick(pr.baselineRun, path);
      const b = pick(pr.candidateRun, path);
      if (typeof a !== "number" || !Number.isFinite(a) || typeof b !== "number" || !Number.isFinite(b)) {
        missing++;
        continue;
      }
      deltas.push(b - a);
      samples.baseline.push(a);
      samples.candidate.push(b);
    }
    if (missing > 0) problems.push(`${label}: ${missing}/${pairs.length} pairs missing the measurement`);
    if (!deltas.length) {
      perMetric[label] = { nPairs: 0, verdict: "INCONCLUSIVE", reason: "no measurable pairs", direction: spec.direction };
      overall = "INCONCLUSIVE";
      continue;
    }
    const medianDelta = percentile(deltas, 50);
    const ci = tCi95(deltas);
    const signConsistent = deltas.every((d) => d >= 0) || deltas.every((d) => d <= 0);
    const outliers = madOutliers(deltas);
    const driftA = driftCheck(samples.baseline, { threshold: spec.regressionThreshold });
    const driftB = driftCheck(samples.candidate, { threshold: spec.regressionThreshold });
    const runBlockers = [...new Set(pairs.flatMap((pr) => [...(pr.baselineRun.blockers || []), ...(pr.candidateRun.blockers || [])]))];
    let verdict;
    const reasons = [];
    if (runBlockers.length) {
      verdict = "INCONCLUSIVE";
      reasons.push(`run blockers: ${runBlockers.join(",")}`);
    } else if (driftA.suspected || driftB.suspected) {
      verdict = "INCONCLUSIVE";
      reasons.push(`drift suspected within an arm (A:${driftA.driftMagnitude} B:${driftB.driftMagnitude} ms) — extend cycles / add cooldown`);
    } else if (deltas.length < minPairs) {
      verdict = "INCONCLUSIVE";
      reasons.push(`insufficient pairs (${deltas.length} < ${minPairs})`);
    } else if (medianDelta >= spec.regressionThreshold && signConsistent && ci.ci && ci.ci[0] > 0) {
      verdict = "REGRESSED";
    } else if (spec.improvementThreshold != null && medianDelta <= -spec.improvementThreshold && signConsistent && ci.ci && ci.ci[1] < 0) {
      verdict = "IMPROVED";
    } else if (ci.ci && ci.ci[0] > -spec.regressionThreshold && ci.ci[1] < spec.regressionThreshold) {
      verdict = "NO_CHANGE";
    } else {
      verdict = "INCONCLUSIVE";
      reasons.push(`medianDelta ${Math.round(medianDelta * 100) / 100} with CI [${ci.ci ? ci.ci.map((x) => Math.round(x * 100) / 100).join(", ") : "n/a"}] spans the threshold (${spec.regressionThreshold})`);
    }
    const d = cohensD(deltas);
    perMetric[label] = {
      path,
      direction: spec.direction || "lower-better",
      nPairs: deltas.length,
      medianDelta: Math.round(medianDelta * 100) / 100,
      ci95: ci.ci ? ci.ci.map((x) => Math.round(x * 100) / 100) : null,
      signConsistent,
      effectSizeDz: d.d,
      outliers: outliers.outliers,
      drift: { baseline: driftA, candidate: driftB },
      verdict,
      reasons,
      claim: deltas.length <= 4 ? "indicative (n<=4 pairs — never a universal significance claim)" : "provisional"
    };
    if (verdict === "REGRESSED") overall = "REGRESSED";
    else if (verdict === "INCONCLUSIVE" && overall !== "REGRESSED") overall = "INCONCLUSIVE";
    else if (verdict === "IMPROVED" && overall === "NO_CHANGE") overall = "IMPROVED";
  }
  const sd = deltasOf(perMetric);
  return { verdict: overall, blockers: problems, perMetric, pairs: pairs.length, cycles: pairing.cycles, sampleSize: sd };
}

function deltasOf(perMetric) {
  const first = Object.values(perMetric)[0];
  return first ? { note: "see perMetric for n" } : null;
}

/**
 * Task D: rendering & memory findings from run receipts. Pure; thresholds explicit; every
 * finding reports its n. Repeating paint => "repainting detected, cause UNATTRIBUTED — a
 * controlled comparison (baseline arm / animation-disabled build) is required before
 * attributing causality to shimmer".
 */
export function renderingFindings(runs, thresholds = {}) {
  const t = {
    maxDrawingLayers: thresholds.maxDrawingLayers ?? 30,
    textureBudgetMB: thresholds.textureBudgetMB ?? 250,
    idlePaintRepeatLimit: thresholds.idlePaintRepeatLimit ?? 5,
    imageDecodeTotalMs: thresholds.imageDecodeTotalMs ?? 50,
    domGrowthNodes: thresholds.domGrowthNodes ?? 500,
    heapGrowthMB: thresholds.heapGrowthMB ?? 20,
    ...thresholds
  };
  const measured = (runs || []).filter((r) => r && r.role !== "warmup");
  const findings = [];
  const n = measured.length;

  const withLayers = measured.filter((r) => r.layers);
  if (withLayers.length) {
    const worst = withLayers.reduce((a, r) => (r.layers.drawing > a.layers.drawing ? r : a), withLayers[0]);
    findings.push({
      id: "compositor-layers",
      n: withLayers.length,
      worstDrawingLayers: worst.layers.drawing,
      totalLayers: worst.layers.layers,
      textureEstimateMB: worst.layers.textureEstimateMB ?? worst.layers.approxMB,
      excessive: worst.layers.drawing > t.maxDrawingLayers,
      threshold: t.maxDrawingLayers,
      note: `texture estimate = sum(layer pixels) x 4B vs ${t.textureBudgetMB} MB budget; observed GPU/process memory is NOT exposed via CDP on this surface — estimate only`
    });
  } else findings.push({ id: "compositor-layers", n: 0, verdict: "NOT_MEASURED" });

  const idleRuns = measured.filter((r) => r.mode === "idle" && r.idle);
  if (idleRuns.length) {
    const rep = idleRuns.filter((r) => r.idle.paint && r.idle.paint.repeating);
    findings.push({
      id: "repeating-paint",
      n: idleRuns.length,
      runsDetectingRepainting: rep.length,
      repeating: rep.length > 0,
      worstRepeatedRectCount: rep.length ? Math.max(...rep.map((r) => r.idle.paint.repeated[0]?.count ?? 0)) : 0,
      causality: rep.length ? "UNATTRIBUTED — repainting is evidence of repaint, not proof of its cause; attribute only via a controlled comparison (baseline arm or animation-disabled build)" : "n/a",
      threshold: t.idlePaintRepeatLimit
    });
  } else findings.push({ id: "repeating-paint", n: 0, verdict: "NOT_MEASURED (idle runs required)" });

  const decodeRuns = measured.filter((r) => r.idle && r.idle.imageDecode);
  if (decodeRuns.length) {
    const worst = decodeRuns.reduce((a, r) => (r.idle.imageDecode.totalMs > (a.idle?.imageDecode?.totalMs ?? 0) ? r : a), decodeRuns[0]);
    findings.push({
      id: "image-decode",
      n: decodeRuns.length,
      decodeCount: worst.idle.imageDecode.count,
      totalMs: worst.idle.imageDecode.totalMs,
      maxMs: worst.idle.imageDecode.maxMs,
      expensive: worst.idle.imageDecode.totalMs > t.imageDecodeTotalMs,
      threshold: t.imageDecodeTotalMs
    });
  } else findings.push({ id: "image-decode", n: 0, verdict: "NOT_MEASURED (trace required)" });

  // DOM/heap growth only within nav/idle runs — across a startup reload the counters reset
  // (new document), so a "delta" there would be absolute-count nonsense.
  const domRuns = measured.filter((r) => (r.mode === "nav" || r.mode === "idle") && r.metrics && Array.isArray(r.metrics.Nodes));
  if (domRuns.length) {
    const growth = domRuns.map((r) => (r.metrics.Nodes[1] ?? 0) - (r.metrics.Nodes[0] ?? 0));
    const net = domRuns.length ? (domRuns[domRuns.length - 1].metrics.Nodes[1] ?? 0) - (domRuns[0].metrics.Nodes[0] ?? 0) : 0;
    findings.push({ id: "dom-growth", n: domRuns.length, perRunGrowth: growth, netAcrossExperiment: net, flagged: Math.max(...growth.map(Math.abs)) > t.domGrowthNodes, threshold: t.domGrowthNodes });
  } else findings.push({ id: "dom-growth", n: 0, verdict: "NOT_MEASURED" });

  const heapRuns = measured.filter((r) => (r.mode === "nav" || r.mode === "idle") && r.metrics && Array.isArray(r.metrics.JSHeapUsedSize));
  if (heapRuns.length) {
    const first = heapRuns[0].metrics.JSHeapUsedSize[0];
    const last = heapRuns[heapRuns.length - 1].metrics.JSHeapUsedSize[1];
    const growthMB = first != null && last != null ? Math.round(((last - first) / 1048576) * 10) / 10 : null;
    findings.push({
      id: "memory-growth",
      n: heapRuns.length,
      jsHeapGrowthMB: growthMB,
      flagged: growthMB != null && growthMB > t.heapGrowthMB,
      threshold: t.heapGrowthMB,
      note: "V8 JS heap only (measured); process memory and GPU memory are NOT exposed here — do not conflate with textureEstimateMB"
    });
  } else findings.push({ id: "memory-growth", n: 0, verdict: "NOT_MEASURED" });

  const navRuns = measured.filter((r) => r.mode === "nav");
  if (navRuns.length) {
    const stalls = navRuns.map((r) => r.frames?.longFrames?.over50ms ?? 0);
    const worstLt = navRuns.reduce((a, r) => Math.max(a, r.longTasks?.maxMs ?? 0), 0);
    findings.push({
      id: "nav-stalls",
      n: navRuns.length,
      longFramesOver50msPerRun: stalls,
      worstLongTaskMs: worstLt,
      note: "frame stalls during guarded navigation — NOT input-latency measurements (keypress timestamps are not recorded)"
    });
  }
  const idleAll = measured.filter((r) => r.mode === "idle");
  if (idleAll.length)
    findings.push({
      id: "idle-activity",
      n: idleAll.length,
      longTasksAtIdle: idleAll.map((r) => r.longTasks?.count ?? 0),
      paintsAtIdle: idleAll.map((r) => r.idle?.paint?.paints ?? null),
      apiRequestsAtIdle: idleAll.map((r) => r.idle?.apiRequests ?? null)
    });
  return { schema: "rendering-findings/1", n, findings };
}

/**
 * Treatment-identity check (Assignment 05B P0/P1): a comparative verdict is only meaningful
 * when every measured run carried a VERIFIED treatment identity. Rejects:
 *   - treatment-identity-unknown      a paired run has no verified theme marker
 *   - treatment-identity-not-distinct both arms observed the SAME identity (mislabeled arms)
 *   - within-arm-identity-drift       an arm measured >1 buildId/asset set (unless permitted)
 *   - source-identity-drift           runs measured against different source SHAs
 * permittedDifferences (manifest.armIdentity.permittedDifferences) may list "buildId",
 * "assets", "sourceSha" — never "theme".
 */
export function treatmentIdentityCheck(runs, manifest = {}) {
  const measured = (runs || []).filter((r) => r && r.role !== "warmup" && r.verdict === "MEASURED");
  const permitted = new Set(manifest.armIdentity?.permittedDifferences || []);
  const problems = [];
  const arms = [...new Set(measured.map((r) => r.arm))];
  if (arms.length === 2) {
    if (measured.some((r) => !r.armIdentity?.observed?.theme)) {
      problems.push(`treatment-identity-unknown: ${measured.filter((r) => !r.armIdentity?.observed?.theme).length}/${measured.length} measured runs have no verified theme marker`);
    } else {
      const perArm = new Map(arms.map((a) => [a, measured.filter((r) => r.arm === a)]));
      for (const [arm, rs] of perArm) {
        const themes = new Set(rs.map((r) => r.armIdentity.observed.theme));
        if (themes.size > 1) problems.push(`within-arm-theme-drift: arm ${arm} observed themes ${[...themes].join("|")}`);
        const buildIds = new Set(rs.map((r) => r.armIdentity.observed.buildId ?? null));
        if (buildIds.size > 1 && !permitted.has("buildId")) problems.push(`within-arm-identity-drift: arm ${arm} measured ${buildIds.size} buildIds (permittedDifferences may allow this)`);
        const assetSets = new Set(rs.map((r) => JSON.stringify((r.armIdentity.observed.assets || []).map((a) => `${a.label}:${a.sha256}`).sort())));
        if (assetSets.size > 1 && !permitted.has("assets")) problems.push(`within-arm-asset-drift: arm ${arm} measured ${assetSets.size} distinct asset-hash sets`);
      }
      if (!problems.length) {
        const identityOf = (arm) => {
          const rs = perArm.get(arm);
          const o = rs[0].armIdentity.observed;
          return JSON.stringify({ theme: o.theme, buildId: o.buildId ?? null, assets: (o.assets || []).map((a) => `${a.label}:${a.sha256}`).sort() });
        };
        if (identityOf(arms[0]) === identityOf(arms[1]))
          problems.push(`treatment-identity-not-distinct: both arms observed identity ${perArm.get(arms[0])[0].armIdentity.observed.theme} — deliberately mislabeled arms cannot produce a comparative verdict`);
      }
    }
  }
  const shas = new Set(measured.map((r) => r.sourceSha).filter(Boolean));
  if (shas.size > 1 && !permitted.has("sourceSha")) problems.push(`source-identity-drift: runs measured against ${shas.size} different source SHAs`);
  return { problems, n: measured.length, checked: arms.length === 2 };
}

/** Top-level pure analysis used by the controller, the report CLI and the tests. */
export function analyzeExperiment(runs, manifest) {
  const measured = (runs || []).filter((r) => r && r.role !== "warmup");
  const blockers = [...new Set(measured.flatMap((r) => r.blockers || []))];
  const aborted = measured.filter((r) => r.verdict !== "MEASURED");
  if (aborted.length) blockers.push(`${aborted.length} run(s) not MEASURED`);
  const identity = treatmentIdentityCheck(measured, manifest);
  let comparison =
    (manifest.mode === "nav" || manifest.mode === "startup") && (manifest.design?.type === "abba" || manifest.arms?.length === 2)
      ? compareMetrics(measured, {
          metrics: manifest.thresholds?.metrics || [{ path: "frames.frameIntervalMs.p90", label: "frame-interval p90", direction: "lower-better", regressionThreshold: manifest.thresholds?.regressionThresholdMs ?? 2, improvementThreshold: manifest.thresholds?.improvementThresholdMs ?? 2 }],
          baseline: manifest.arms[0].label,
          candidate: manifest.arms[1].label,
          minPairs: manifest.thresholds?.minPairs ?? 4
        })
      : { verdict: "DESCRIBED", note: "single-arm or non-nav design: no pairing (reported descriptively)", perMetric: {} };
  // Treatment identity gates the verdict: unknown / not-distinct / drifting identity can
  // never surface IMPROVED or REGRESSED — only INCONCLUSIVE with the problem named.
  if (identity.problems.length) {
    comparison = { ...comparison, verdict: "INCONCLUSIVE", identityProblems: identity.problems };
  }
  const firstDeltaMetric = Object.values(comparison.perMetric || {})[0];
  const guidance =
    firstDeltaMetric && firstDeltaMetric.ci95
      ? sampleSizeGuidance({ sdDelta: sdFromCi(firstDeltaMetric), worthwhileDelta: manifest.worthwhileEffectMs, currentPairs: firstDeltaMetric.nPairs })
      : { note: "guidance unavailable (no paired metric)" };
  return {
    schema: "nuvio-exp-verdict/1",
    experiment: manifest.id,
    surface: manifest.surface,
    mode: manifest.mode,
    design: manifest.design,
    arms: (manifest.arms || []).map((a) => a.label),
    runsMeasured: measured.length,
    runsAborted: aborted.length,
    nRuns: measured.length,
    treatmentIdentity: identity,
    comparison,
    sampleSizeGuidance: guidance,
    rendering: renderingFindings(measured, manifest.thresholds?.rendering),
    blockers,
    verdict: blockers.length ? "INCOMPLETE" : comparison.verdict,
    note: "every number reports its n; frames are autocorrelated within a run and are never treated as independent replicates"
  };
}

/** Recover an SD estimate from a reported CI (width / 2t) — for guidance only. */
function sdFromCi(metric) {
  if (!metric.ci95 || metric.nPairs < 2) return 0;
  const t = metric.nPairs - 2 < T95.length ? T95[metric.nPairs - 2] : 1.96;
  const half = (metric.ci95[1] - metric.ci95[0]) / 2;
  return (half * Math.sqrt(metric.nPairs)) / t;
}
