// Task C fixtures: every statistical function is tested against hand-computed known outcomes.
// Pure module — no CDP, no fs. If these fail, the mathematics changed, not the environment.
import { test } from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const perfDir = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "perf");
const S = await import(pathToFileURL(path.join(perfDir, "stats.mjs")).href);

test("nearest-rank percentiles: exact order statistics, no interpolation", () => {
  // sorted [16,16,17,50]: p50 rank 2 -> 16; p90 rank ceil(3.6)=4 -> 50; p95 rank 4 -> 50
  assert.equal(S.nearestRank([17, 16, 50, 16], 50), 16);
  assert.equal(S.nearestRank([17, 16, 50, 16], 90), 50);
  assert.equal(S.nearestRank([17, 16, 50, 16], 95), 50);
  assert.equal(S.nearestRank([1], 99), 1); // n=1: every percentile is the sample
  assert.equal(S.nearestRank([], 50), null);
});

test("t-CI (95%, Student): hand-computed fixture [10,12,14,16]", () => {
  // mean 13, sample sd sqrt(20/3)=2.5820, se 1.2910, t(df=3)=3.1824 -> 13 +/- 4.1085
  const r = S.tCi95([10, 12, 14, 16]);
  assert.equal(r.n, 4);
  assert.equal(r.mean, 13);
  assert.ok(Math.abs(r.ci[0] - 8.8915) < 0.001, `ci[0]=${r.ci[0]}`);
  assert.ok(Math.abs(r.ci[1] - 17.1085) < 0.001, `ci[1]=${r.ci[1]}`);
  assert.equal(S.tCi95([5]).ci, null); // single sample: no CI
  assert.equal(S.tCi95([]).ci, null);
  const zero = S.tCi95([7, 7, 7, 7]);
  assert.deepEqual(zero.ci, [7, 7]);
  assert.equal(zero.zeroVariance, true);
});

test("Cohen's d (paired): known value + zero-variance refusal", () => {
  // deltas [2,4,6,8]: mean 5, sd sqrt(6.667)=2.582 -> d = 1.936
  const r = S.cohensD([2, 4, 6, 8]);
  assert.ok(Math.abs(r.d - 1.936) < 0.001, `d=${r.d}`);
  const z = S.cohensD([3, 3, 3, 3]);
  assert.equal(z.d, null);
  assert.equal(z.zeroVariance, true); // never a fabricated effect size
});

test("MAD outliers: planted outlier flagged, clean set clean, MAD=0 fallback works", () => {
  const planted = S.madOutliers([10, 10.2, 9.8, 10.1, 9.9, 10, 10.2, 9.8, 10.1, 100]);
  assert.equal(planted.outliers.length, 1);
  assert.equal(planted.outliers[0].value, 100);
  assert.ok(planted.outliers[0].modifiedZ > 3.5);
  const clean = S.madOutliers([10, 10.5, 11, 9.5, 10.2, 9.9]);
  assert.equal(clean.outliers.length, 0); // flagged, never deleted either way
  const zeroMad = S.madOutliers([10, 10, 10, 10, 10, 10, 10, 10, 10, 100]);
  assert.equal(zeroMad.madFallbackUsed, true);
  assert.equal(zeroMad.outliers.length, 1);
});

test("drift detection: monotonic within-arm shift is caught; stable series is not", () => {
  const drifting = S.driftCheck([10, 10, 10, 10, 20, 20, 20, 20], { threshold: 2 });
  assert.equal(drifting.suspected, true);
  assert.equal(drifting.driftMagnitude, 10);
  const stable = S.driftCheck([10, 11, 10, 11, 10, 11, 10, 11], { threshold: 2 });
  assert.equal(stable.suspected, false);
  const short = S.driftCheck([10, 11], { threshold: 2 });
  assert.equal(short.suspected, false); // n<4: no drift test, no false claim
});

test("A/B/B/A pairing: adjacent pairs, delta = candidate - baseline, validation errors", () => {
  const run = (arm, cycle, position, p90) => ({ role: "measured", verdict: "MEASURED", arm, cycle, position, frames: { frameIntervalMs: { p90 } } });
  const runs = [run("A", 1, 1, 20), run("B", 1, 2, 17), run("B", 1, 3, 18), run("A", 1, 4, 21)];
  const p = S.pairAbba(runs, { baseline: "A", candidate: "B" });
  assert.equal(p.error, undefined);
  assert.equal(p.pairs.length, 2);
  assert.equal(p.pairs[0].baselineRun.frames.frameIntervalMs.p90, 20); // pos1 A with pos2 B
  assert.equal(p.pairs[1].baselineRun.frames.frameIntervalMs.p90, 21); // pos4 A with pos3 B
  // wrong order (A,B,A,B) is rejected:
  const bad = S.pairAbba([run("A", 1, 1, 20), run("B", 1, 2, 17), run("A", 1, 3, 18), run("B", 1, 4, 21)], { baseline: "A", candidate: "B" });
  assert.ok(bad.error.includes("A/B/B/A"));
  // missing runs rejected:
  const missing = S.pairAbba(runs.slice(0, 3), { baseline: "A", candidate: "B" });
  assert.ok(missing.error.includes("expected 4"));
  // warmup runs are excluded from pairing:
  const withWarmup = [...runs, { role: "warmup", verdict: "MEASURED", arm: "A", cycle: 1, position: 0 }];
  const p2 = S.pairAbba(withWarmup, { baseline: "A", candidate: "B" });
  assert.equal(p2.pairs.length, 2);
  // a stray extra measured run inside a cycle makes the cycle invalid (5 != 4):
  const withExtra = [...runs, run("A", 1, 5, 22)];
  const p3 = S.pairAbba(withExtra, { baseline: "A", candidate: "B" });
  assert.ok(p3.error.includes("expected 4"));
});

test("compareMetrics: REGRESSED / NO_CHANGE / INCONCLUSIVE fixtures", () => {
  const mk = (deltas, opts = {}) => {
    const runs = [];
    let cycle = 1;
    for (let i = 0; i < deltas.length; i += 2) {
      const [d1, d2] = [deltas[i], deltas[i + 1]];
      runs.push({ role: "measured", verdict: "MEASURED", arm: "A", cycle, position: 1, frames: { frameIntervalMs: { p90: 20 } } });
      runs.push({ role: "measured", verdict: "MEASURED", arm: "B", cycle, position: 2, frames: { frameIntervalMs: { p90: 20 + d1 } } });
      runs.push({ role: "measured", verdict: "MEASURED", arm: "B", cycle, position: 3, frames: { frameIntervalMs: { p90: 20 + d2 } } });
      runs.push({ role: "measured", verdict: "MEASURED", arm: "A", cycle, position: 4, frames: { frameIntervalMs: { p90: 20 } } });
      cycle++;
    }
    return runs;
  };
  const spec = { metrics: [{ path: "frames.frameIntervalMs.p90", label: "p90", direction: "lower-better", regressionThreshold: 2, improvementThreshold: 2 }], baseline: "A", candidate: "B", minPairs: 4 };
  // all deltas +5, same sign, CI excludes 0 -> REGRESSED
  const reg = S.compareMetrics(mk([5, 5, 5, 5, 5, 5, 5, 5]), spec);
  assert.equal(reg.perMetric.p90.verdict, "REGRESSED", JSON.stringify(reg.perMetric.p90));
  assert.equal(reg.perMetric.p90.signConsistent, true);
  assert.ok(reg.perMetric.p90.ci95[0] > 0);
  // mixed signs -> INCONCLUSIVE (never a fabricated verdict)
  const mixed = S.compareMetrics(mk([5, -5, 5, -5, 5, -5, 5, -5]), spec);
  assert.equal(mixed.perMetric.p90.verdict, "INCONCLUSIVE");
  // tiny consistent deltas (+0.2, CI inside +-2) -> NO_CHANGE
  const nc = S.compareMetrics(mk([0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2]), spec);
  assert.equal(nc.perMetric.p90.verdict, "NO_CHANGE", JSON.stringify(nc.perMetric.p90));
  // fewer pairs than minPairs -> INCONCLUSIVE with reason
  const few = S.compareMetrics(mk([5, 5]), { ...spec, minPairs: 4 });
  assert.equal(few.perMetric.p90.verdict, "INCONCLUSIVE");
  assert.ok(few.perMetric.p90.reasons.join(" ").includes("insufficient"));
  // <=4 pairs is labelled indicative, never significant; >4 is provisional
  assert.ok(reg.perMetric.p90.claim.includes("provisional")); // 8 pairs here
  const four = S.compareMetrics(mk([5, 5, 5, 5]), spec);
  assert.equal(four.perMetric.p90.verdict, "REGRESSED");
  assert.ok(four.perMetric.p90.claim.includes("indicative"));
});

test("compareMetrics: run blockers and missing measurements force INCONCLUSIVE", () => {
  const run = (arm, cycle, position, p90, extra = {}) => ({ role: "measured", verdict: "MEASURED", arm, cycle, position, frames: p90 == null ? null : { frameIntervalMs: { p90 } }, blockers: [], ...extra });
  const runs = [
    run("A", 1, 1, 20), run("B", 1, 2, 25), run("B", 1, 3, 25), run("A", 1, 4, 20),
    run("A", 2, 1, 20, { blockers: ["frame-clock-anomaly"] }), run("B", 2, 2, 25), run("B", 2, 3, null), run("A", 2, 4, 20)
  ];
  const r = S.compareMetrics(runs, { metrics: [{ path: "frames.frameIntervalMs.p90", label: "p90", direction: "lower-better", regressionThreshold: 2 }], baseline: "A", candidate: "B", minPairs: 4 });
  assert.equal(r.perMetric.p90.verdict, "INCONCLUSIVE");
  assert.ok(r.perMetric.p90.reasons.join(" ").includes("blockers"));
  assert.ok(r.blockers.some((b) => b.includes("missing")));
  assert.equal(r.perMetric.p90.nPairs, 3); // cycle1: 2 measurable pairs; cycle2: 1 (the B-null pair is missing)
});

test("sample-size guidance: known formula output", () => {
  // (1.96+0.8416)*sd/delta squared: sd=2, delta=1 -> (5.6032)^2 = 31.4 -> 32 pairs
  const g = S.sampleSizeGuidance({ sdDelta: 2, worthwhileDelta: 1, currentPairs: 8 });
  assert.equal(g.requiredPairs, 32);
  assert.equal(g.currentPairs, 8);
  const none = S.sampleSizeGuidance({ sdDelta: 0, worthwhileDelta: 1, currentPairs: 8 });
  assert.equal(none.requiredPairs, null); // zero variance: guidance unavailable, not invented
});

test("frameStats: refresh/dropped/long-frame arithmetic on a 60 Hz fixture", () => {
  // 19 vsync gaps + TWO 50 ms stalls (n=21): nearest-rank p95 = rank ceil(19.95)=20 -> sorted[19] = 50
  const gaps = [...Array(19).fill(16.7), 50, 50];
  const f = S.frameStats(gaps);
  assert.equal(f.refreshEstimate.hz, 60);
  assert.equal(f.droppedFrames.count, 2); // each 50 >= 2 x 16.67
  assert.equal(f.longFrames.over50ms, 0); // strictly greater
  assert.equal(f.longFrames.over33ms, 2);
  assert.equal(f.frameIntervalMs.median, 16.7);
  assert.equal(f.fpsImpliedByPercentileInterval.fromP95, 20); // 1000/50 — an inversion, not an fps percentile
  assert.equal(f.instantaneousFps.min, 20); // worst per-frame fps sample
  assert.ok(f.fpsImpliedByPercentileInterval.fromP95 <= f.instantaneousFps.p05 + 0.1);
});

test("analyzeExperiment: end-to-end verdict assembly with n reported everywhere", () => {
  const idOf = (arm) => ({ observed: { theme: arm, buildId: arm === "gh2" ? "build-gh2-1" : "build-classic-1", assets: [{ label: "dash", sha256: arm === "gh2" ? "bb" : "aa" }] } });
  const run = (arm, cycle, position, p90) => ({ role: "measured", verdict: "MEASURED", arm, cycle, position, mode: "nav", armIdentity: idOf(arm), frames: S.frameStats(Array(30).fill(p90)), longTasks: { count: 0, maxMs: 0, over50ms: 0, totalMs: 0 }, metrics: null, blockers: [] });
  const runs = [];
  for (let c = 1; c <= 4; c++) {
    runs.push(run("classic", c, 1, 20), run("gh2", c, 2, 17), run("gh2", c, 3, 17), run("classic", c, 4, 20));
  }
  const manifest = {
    id: "GHUI-1", mode: "nav", surface: "desktop", design: { type: "abba", cycles: 4 },
    arms: [{ label: "classic" }, { label: "gh2" }],
    thresholds: { metrics: [{ path: "frames.frameIntervalMs.p90", label: "p90", direction: "lower-better", regressionThreshold: 2, improvementThreshold: 2 }], minPairs: 4 },
    worthwhileEffectMs: 3
  };
  const a = S.analyzeExperiment(runs, manifest);
  assert.equal(a.verdict, "IMPROVED");
  assert.equal(a.runsMeasured, 16);
  assert.equal(a.comparison.pairs, 8);
  assert.equal(a.comparison.perMetric.p90.nPairs, 8);
  assert.equal(a.comparison.perMetric.p90.medianDelta, -3);
  assert.ok(a.sampleSizeGuidance.requiredPairs != null || a.sampleSizeGuidance.note != null);
  assert.ok(a.note.includes("autocorrelated"));
  // TREATMENT-IDENTITY GATE (05B): mislabeled arms can never produce IMPROVED.
  // (a) identity unknown (no verified theme) -> INCONCLUSIVE
  const unknownId = runs.map((r) => ({ ...r, armIdentity: undefined }));
  const ua = S.analyzeExperiment(unknownId, manifest);
  assert.notEqual(ua.verdict, "IMPROVED");
  assert.notEqual(ua.comparison.verdict, "IMPROVED");
  assert.equal(ua.comparison.verdict, "INCONCLUSIVE");
  assert.ok(ua.comparison.identityProblems.some((p) => p.includes("treatment-identity-unknown")));
  // (b) both arms actually observed the SAME theme (labels lie) -> not distinct -> INCONCLUSIVE
  const mislabeled = runs.map((r) => ({ ...r, armIdentity: idOf("classic") }));
  const ma = S.analyzeExperiment(mislabeled, manifest);
  assert.notEqual(ma.verdict, "IMPROVED");
  assert.equal(ma.comparison.verdict, "INCONCLUSIVE");
  assert.ok(ma.comparison.identityProblems.some((p) => p.includes("treatment-identity-not-distinct")));
  // (c) within-arm build drift without permission -> INCONCLUSIVE; with permission -> allowed
  const drifted = runs.map((r) => (r.arm === "gh2" ? { ...r, armIdentity: { observed: { ...r.armIdentity.observed, buildId: r.cycle % 2 ? "build-gh2-1" : "build-gh2-2" } } } : r));
  const da = S.analyzeExperiment(drifted, manifest);
  assert.equal(da.comparison.verdict, "INCONCLUSIVE");
  assert.ok(da.comparison.identityProblems.some((p) => p.includes("within-arm-identity-drift")));
  const permitted = S.analyzeExperiment(drifted, { ...manifest, armIdentity: { permittedDifferences: ["buildId"] } });
  assert.equal(permitted.comparison.verdict, "IMPROVED"); // explicitly permitted by design
  // (d) source drift across runs -> INCONCLUSIVE unless permitted
  const srcDrift = runs.map((r, i) => ({ ...r, sourceSha: i < 8 ? "sha-1" : "sha-2" }));
  const sa = S.analyzeExperiment(srcDrift, manifest);
  assert.equal(sa.comparison.verdict, "INCONCLUSIVE");
  assert.ok(sa.comparison.identityProblems.some((p) => p.includes("source-identity-drift")));

  // single-arm idle manifest -> descriptive, no pairing, no fabricated comparison
  const b = S.analyzeExperiment([{ role: "measured", verdict: "MEASURED", arm: "gh2", mode: "idle", idle: { paint: { repeating: true, repeated: [{ count: 9 }] } }, frames: S.frameStats([16, 17]), longTasks: { count: 1, maxMs: 60, over50ms: 1, totalMs: 60 }, blockers: [] }], { id: "GHUI-3", mode: "idle", surface: "desktop", arms: [{ label: "gh2" }] });
  assert.equal(b.comparison.verdict, "DESCRIBED");
  const paint = b.rendering.findings.find((x) => x.id === "repeating-paint");
  assert.equal(paint.repeating, true);
  assert.ok(paint.causality.includes("UNATTRIBUTED"));
});
