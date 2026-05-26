import { NextRequest, NextResponse } from 'next/server';

const HERMES = process.env.HERMES_URL_INTERNAL ?? 'http://hermes:8080';

export async function POST(request: NextRequest) {
  let body: { text?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const { text } = body;
  if (!text || typeof text !== 'string' || text.trim().length === 0) {
    return NextResponse.json({ error: 'text field is required' }, { status: 400 });
  }

  let res: Response;
  try {
    res = await fetch(`${HERMES}/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text.trim() }),
      signal: AbortSignal.timeout(10000),
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'hermes unreachable';
    return NextResponse.json({ error: msg }, { status: 503 });
  }

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
