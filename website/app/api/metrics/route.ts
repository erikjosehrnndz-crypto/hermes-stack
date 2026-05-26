import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const HERMES = process.env.HERMES_URL_INTERNAL ?? 'http://hermes:8080';
const LITELLM = process.env.LITELLM_URL_INTERNAL ?? 'http://litellm:4000';
const LITELLM_KEY = process.env.LITELLM_MASTER_KEY ?? '';

function parsePrometheus(text: string): Record<string, number> {
  const out: Record<string, number> = {};
  for (const line of text.split('\n')) {
    if (line.startsWith('#') || !line.trim()) continue;
    const m = line.match(/^([^\s{]+(?:\{[^}]*\})?)\s+([\d.e+\-]+)/);
    if (m) out[m[1]] = parseFloat(m[2]);
  }
  return out;
}

export async function GET() {
  const abort = { signal: AbortSignal.timeout(3000) };

  const [healthRes, metricsRes, litellmRes] = await Promise.allSettled([
    fetch(`${HERMES}/health`, abort),
    fetch(`${HERMES}/metrics`, abort),
    fetch(`${LITELLM}/health`, {
      ...abort,
      headers: LITELLM_KEY ? { Authorization: `Bearer ${LITELLM_KEY}` } : {},
    }),
  ]);

  let hermesUp = false;
  let hermesChecks: Record<string, boolean> = {};
  if (healthRes.status === 'fulfilled') {
    const r = healthRes.value;
    hermesUp = r.ok || r.status === 200;
    if (hermesUp) {
      const body = await r.json().catch(() => ({}));
      hermesChecks = (body.checks as Record<string, boolean>) ?? {};
    }
  }

  let raw: Record<string, number> = {};
  if (metricsRes.status === 'fulfilled' && metricsRes.value.ok) {
    raw = parsePrometheus(await metricsRes.value.text());
  }

  let litellmUp = false;
  if (litellmRes.status === 'fulfilled') {
    litellmUp = [200, 401].includes(litellmRes.value.status);
  }

  const ok200 = raw['hermes_http_requests_total{method="POST",endpoint="/process",status="200"}'] ?? 0;
  const ok400 = raw['hermes_http_requests_total{method="POST",endpoint="/process",status="400"}'] ?? 0;
  const ok500 = raw['hermes_http_requests_total{method="POST",endpoint="/process",status="500"}'] ?? 0;
  const totalReqs = ok200 + ok400 + ok500;
  const latSum = raw['hermes_process_latency_seconds_sum'] ?? 0;
  const latCount = raw['hermes_process_latency_seconds_count'] ?? 0;
  const avgLatMs = latCount > 0 ? Math.round((latSum / latCount) * 1000) : null;
  const errorRate = totalReqs > 0 ? Math.round(((ok500) / totalReqs) * 1000) / 10 : 0;

  return NextResponse.json({
    ts: Date.now(),
    services: {
      hermes: { up: hermesUp, checks: hermesChecks },
      litellm: { up: litellmUp },
    },
    metrics: {
      totalRequests: Math.round(totalReqs),
      successRequests: Math.round(ok200),
      avgLatencyMs: avgLatMs,
      errorRatePct: errorRate,
    },
  });
}
