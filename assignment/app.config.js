const baseConfig = require('./app.json');

// Only the public FastAPI backend URL is exposed to the app. Provider
// credentials remain on the backend and never enter the mobile bundle.
module.exports = () => ({
  ...baseConfig.expo,
  extra: {
    ...(baseConfig.expo.extra || {}),
    songApiUrl: process.env.EXPO_PUBLIC_SONG_API_URL || '',
  },
});
