# IoV Admin Dashboard Frontend

Files:
- index.html
- styles.css
- app.js

## Features
- Admin monitoring dashboard
- Health and Ethereum status
- JSON input sender for `/api/predict`
- Trust lookup for `/api/trust/<vehicle_id>`
- Shard monitoring from `/api/shards`
- Blockchain viewer from `/api/chain`
- Architecture panel from `/api/architecture`

## Run
Open `index.html` in a browser.

If your Flask backend runs on a different URL, change the API Base URL in the sidebar.

## Recommended
Serve the frontend using a simple local server:
- Python:
  `python -m http.server 8080`

Then open:
- `http://127.0.0.1:8080`