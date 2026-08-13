const API_BASE = '/api/v1';

async function parseError(res) {
  let detail = res.statusText;
  try {
    const body = await res.json();
    detail = body.detail || JSON.stringify(body);
  } catch {
    // keep statusText
  }
  throw new Error(detail);
}

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function fetchAnalysis() {
  const res = await fetch(`${API_BASE}/analysis`);
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function uploadDrawing(file) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_BASE}/analyze`, { method: 'POST', body: form });
  if (!res.ok) await parseError(res);
  return res.json();
}

export async function pollJob(jobId, { intervalMs = 2000, onProgress } = {}) {
  while (true) {
    const res = await fetch(`${API_BASE}/jobs/${jobId}`);
    if (!res.ok) await parseError(res);
    const job = await res.json();
    onProgress?.(job);
    if (job.status === 'completed') return job.result;
    if (job.status === 'failed') throw new Error(job.error || 'Pipeline failed');
    await new Promise((r) => setTimeout(r, intervalMs));
  }
}

export async function askQuestion(question) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) await parseError(res);
  return res.json();
}
