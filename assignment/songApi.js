import Constants from 'expo-constants';

const appExtra = Constants.expoConfig?.extra || {};
const SONG_API_URL = (process.env.EXPO_PUBLIC_SONG_API_URL || appExtra.songApiUrl || '').replace(/\/$/, '');

function getErrorMessage(payload, fallback) {
  return typeof payload?.detail === 'string' ? payload.detail : payload?.message || fallback;
}

// Calls the Python FastAPI backend. Groq, Sarvam, FFmpeg and all provider
// credentials remain on the server and are never put into the mobile app.
export async function createSong({ name, language, style = 'birthday' }) {
  if (!SONG_API_URL) {
    throw new Error('Song backend URL is not configured. Set EXPO_PUBLIC_SONG_API_URL.');
  }
  const response = await fetch(`${SONG_API_URL}/generate-song`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, language, style }),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(getErrorMessage(payload, 'Song generation failed.'));
  if (!Array.isArray(payload.lyrics) || payload.lyrics.length !== 4 || !payload.audio_url) {
    throw new Error('The song backend returned an invalid response.');
  }
  return { lines: payload.lyrics, audioUrl: payload.audio_url, cached: Boolean(payload.cached) };
}
