# VK Event Organizer

Static event organizer website ready for Vercel deployment.

## Vercel Deploy

- Framework preset: `Other`
- Build command: leave empty
- Output directory: leave empty
- Root route `/` is handled by `vercel.json`

Private/local files such as `enquiries.json` and `server.py` are excluded from Vercel through `.vercelignore`.

## Production Database

For live enquiry saving and image uploads, paste your Google Apps Script Web App URL in `site-config.js`:

```js
window.VK_CONFIG = {
  SHEET_DB_URL: "https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec"
};
```

Without this URL, the deployed site still opens normally, but enquiries and uploads run in preview/configuration mode.

## Local Preview

```bash
python3 server.py
```

Then open `http://localhost:8000/`.
