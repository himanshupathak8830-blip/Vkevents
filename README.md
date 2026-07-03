# VK Event Organizer

Static event organizer website ready for Vercel deployment.

## Vercel Deploy

- Framework preset: `Other`
- Build command: leave empty
- Output directory: leave empty
- Root route `/` is handled by `vercel.json`
- `index.html` redirects to the main event page so static hosts can open the site without custom routing.

Private/local files such as `enquiries.json` and `server.py` are excluded from Vercel through `.vercelignore`.

## GitHub Pages Warning

If GitHub Actions shows a warning like `Node.js 20 is deprecated` for `actions/checkout@v4` or `actions/upload-artifact@v4`, it is coming from GitHub's generated Pages workflow. It is not a Vercel build error. For Vercel-only deployment, disable GitHub Pages in repository settings or ignore that Pages workflow.

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
