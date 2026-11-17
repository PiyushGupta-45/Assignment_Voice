const ALLOWED_LANGUAGES = new Set([
  'English (India)', 'Hindi', 'Punjabi', 'Bhojpuri', 'Bengali', 'Marathi',
  'Gujarati', 'Tamil', 'Telugu', 'Kannada', 'Malayalam', 'Haryanvi', 'Odia', 'Urdu',
]);
const WINDOW_MS = 60_000;
const MAX_REQUESTS_PER_WINDOW = 2;
const recentRequests = new Map();

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
};

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
  });
}

function tooManyRequests(ip) {
  const now = Date.now();
  const entries = (recentRequests.get(ip) || []).filter((time) => now - time < WINDOW_MS);
  if (entries.length >= MAX_REQUESTS_PER_WINDOW) return true;
  entries.push(now);
  recentRequests.set(ip, entries);
  return false;
}

function providerError(payload, fallback) {
  return payload?.error?.message || payload?.error || payload?.message || fallback;
}

async function createLyrics({ name, language, env }) {
  const prompt = [
    `Write exactly six short, original ${language} song lyric lines for a person named ${name}.`,
    'Make the lyrics catchy, cheerful, family-friendly, rhythmic and like a real song, not a poem.',
    `Write in authentic ${language}. Include ${name} naturally in line three and line six.`,
    'No headings, numbering, explanations, emojis, quotation marks, or extra text.',
    'Return only JSON with this exact shape: {"lines":["line 1","line 2","line 3","line 4","line 5","line 6"]}.',
  ].join(' ');

  const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
    method: 'POST',
    headers: { Authorization: `Bearer ${env.GROQ_API_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: env.GROQ_MODEL || 'openai/gpt-oss-20b',
      messages: [{ role: 'user', content: prompt }],
      reasoning_effort: 'low',
      reasoning_format: 'hidden',
      max_completion_tokens: 700,
      temperature: 0.85,
      response_format: { type: 'json_object' },
    }),
  });
  const payload = await response.json().catch(() => ({}));
  const content = payload?.choices?.[0]?.message?.content || '';
  let lines = [];
  try { lines = JSON.parse(content).lines || []; } catch {}
  lines = lines.map((line) => String(line).trim()).filter(Boolean).slice(0, 6);
  if (!response.ok || lines.length !== 6) {
    throw new Error(providerError(payload, 'Groq could not create six lyric lines.'));
  }
  return lines;
}

function musicStyleFor(language) {
  const styles = {
    Hindi: 'uplifting Bollywood pop, melodic vocal, tabla and light percussion',
    Punjabi: 'energetic Punjabi pop, dhol rhythm, catchy melodic vocal',
    Bhojpuri: 'bright Bhojpuri folk-pop, dholak rhythm, warm vocal',
    Bengali: 'sweet Bengali melodic pop, acoustic instruments, expressive vocal',
    Marathi: 'Marathi pop-folk, dhol-tasha energy, celebratory vocal',
    Gujarati: 'Gujarati garba-pop, dandiya rhythm, joyful vocal',
    Tamil: 'Tamil film-pop, rhythmic percussion, melodic vocal',
    Telugu: 'Telugu film-pop, upbeat beat, expressive vocal',
    Kannada: 'Kannada pop, warm melody, light percussion and vocal',
    Malayalam: 'Malayalam melodic pop, gentle rhythm, soulful vocal',
    Haryanvi: 'Haryanvi desi pop, punchy beat, confident vocal',
    Odia: 'Odia folk-pop, gentle melody, bright vocal',
    Urdu: 'Urdu Sufi-pop, soft strings, expressive vocal',
    'English (India)': 'Indian indie pop, catchy melody, warm lead vocal',
  };
  return styles[language] || 'catchy contemporary pop, warm lead vocal, light percussion';
}

function blueMetalPrompt({ name, language, lines }) {
  // `lines` are inserted verbatim. They are never translated, regenerated, or edited.
  return [
    `Create an original ${language} personalized song for ${name}.`,
    `Style: ${musicStyleFor(language)}. Include singing vocals and full background music.`,
    'Sing the following lyrics exactly as written. Do not rewrite, translate, add, or remove any lyric line:',
    lines.join('\n'),
  ].join('\n\n');
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return new Response(null, { headers: corsHeaders });
    const url = new URL(request.url);
    const taskMatch = url.pathname.match(/^\/song\/([^/]+)$/);

    if (request.method === 'POST' && url.pathname === '/song') {
      const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
      if (tooManyRequests(ip)) return json({ error: 'Please wait before creating another song.' }, 429);
      if (!env.GROQ_API_KEY || !env.BLUEMETAL_API_KEY) {
        return json({ error: 'Song service is not configured on the server.' }, 503);
      }

      let input;
      try { input = await request.json(); } catch { return json({ error: 'Invalid request.' }, 400); }
      const name = typeof input.name === 'string' ? input.name.trim().slice(0, 60) : '';
      const language = typeof input.language === 'string' ? input.language : '';
      if (!name || !ALLOWED_LANGUAGES.has(language)) {
        return json({ error: 'Enter a name and select a supported language.' }, 400);
      }

      try {
        const lines = await createLyrics({ name, language, env });
        const musicResponse = await fetch('https://api.bluemetal.ai/v1/music/generations', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${env.BLUEMETAL_API_KEY}`,
            'Content-Type': 'application/json',
            'Idempotency-Key': crypto.randomUUID(),
          },
          body: JSON.stringify({
            prompt: blueMetalPrompt({ name, language, lines }),
            format: 'mp3',
          }),
        });
        const task = await musicResponse.json().catch(() => ({}));
        if (!musicResponse.ok || !task?.id) {
          return json({ error: providerError(task, 'BlueMetal could not start the song.'), lines }, 502);
        }

        // Send the exact Groq output to the app; the same `lines` were just sent to BlueMetal.
        return json({ taskId: String(task.id), status: task.status || 'queued', lines });
      } catch (error) {
        return json({ error: error instanceof Error ? error.message : 'Song generation failed.' }, 502);
      }
    }

    if (request.method === 'GET' && taskMatch) {
      if (!env.BLUEMETAL_API_KEY) return json({ error: 'Song service is not configured on the server.' }, 503);
      const taskId = decodeURIComponent(taskMatch[1]);
      const response = await fetch(`https://api.bluemetal.ai/v1/music/generations/${encodeURIComponent(taskId)}`, {
        headers: { Authorization: `Bearer ${env.BLUEMETAL_API_KEY}` },
      });
      const task = await response.json().catch(() => ({}));
      if (!response.ok) return json({ error: providerError(task, 'Could not check song status.') }, 502);

      const status = String(task.status || 'queued').toLowerCase();
      return json({
        taskId,
        status: status === 'succeeded' ? 'completed' : status === 'failed' || status === 'canceled' ? 'failed' : 'processing',
        audioUrl: status === 'succeeded' ? task?.audio?.url || null : null,
        error: status === 'failed' || status === 'canceled' ? providerError(task, 'Song generation failed.') : null,
        usage: task?.usage || null,
      });
    }

    return json({ error: 'Use POST /song or GET /song/:taskId.' }, 404);
  },
};
