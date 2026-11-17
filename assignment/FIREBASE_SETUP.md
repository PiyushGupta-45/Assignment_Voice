# Enable private lyric saving (free)

This app stores only a name, selected language, generated lyric lines, an anonymous owner ID, and a timestamp. It never uploads microphone audio.

1. Create a project in the [Firebase console](https://console.firebase.google.com/) and keep it on the **Spark** plan. Do not attach a billing account.
2. Add a Web app to the project and copy its configuration values.
3. Copy `.env.example` to `.env` and fill in the copied values. Do not commit `.env`.
4. In **Authentication → Sign-in method**, enable **Anonymous**.
5. In **Firestore Database**, create a database in production mode. Open the **Rules** tab, replace the rules with [firestore.rules](./firestore.rules), and publish.

The Spark free tier includes 20,000 document writes/day, 50,000 reads/day, and 1 GiB storage. If the quota is exceeded, Firestore stops serving the request rather than billing you; use the Firebase Usage dashboard to monitor it. Do not upgrade to Blaze unless you deliberately want usage-based billing.
