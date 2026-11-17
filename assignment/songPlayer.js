import { Audio } from 'expo-av';

let sound = null;

export async function loadSongAudio(uri, onStatus) {
  await unloadSongAudio();
  await Audio.setAudioModeAsync({ playsInSilentModeIOS: true });
  const created = await Audio.Sound.createAsync(
    { uri, overrideFileExtensionAndroid: 'mp3' },
    { shouldPlay: false },
    onStatus,
  );
  sound = created.sound;
  return sound;
}

export async function toggleSongPlayback() {
  if (!sound) return false;
  const status = await sound.getStatusAsync();
  if (!status.isLoaded) return false;
  if (status.isPlaying) await sound.pauseAsync();
  else await sound.playAsync();
  return !status.isPlaying;
}

export async function seekSong(positionMillis) {
  if (sound) await sound.setPositionAsync(Math.max(0, positionMillis));
}

export async function unloadSongAudio() {
  if (!sound) return;
  try { await sound.unloadAsync(); } finally { sound = null; }
}
