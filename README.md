# Study Circle

A responsive, dependency-free study group matcher. Students choose a course, available times, preferred study style, and meeting format; compatible sample groups are ranked immediately.

## Run locally

```bash
python3 -m http.server 4173
```

Open <http://localhost:4173> in a browser.

## Test

```bash
node --test app.test.js
```

The prototype stores its sample group data in `app.js`, so no database or build step is required.
