# SUFS Manager

Generates SUFS catalog upload workbooks and imports new SUFS orders through a small web app.

## Run with Docker

Build the image:

```sh
docker build -t sufs-manager .
```

Run the web app and write generated files to `./output`:

```sh
mkdir -p output
docker run --rm \
  --env-file .env \
  -p 8000:8000 \
  -v "$(pwd)/output:/app/output" \
  sufs-manager
```

Open `http://localhost:8000`, then use either:

- **Generate Files** to create downloadable catalog export files.
- **Import Orders** to pull new Ariba orders and create Odoo sales orders.

Create `.env` from `.env.example` and set `ODOO_PASSWORD` before running.

Or use Docker Compose:

```sh
mkdir -p output
docker compose up --build
```

## Configuration

| Variable | Required | Default |
| --- | --- | --- |
| `ODOO_URL` | No | `https://riss-group-corzic.odoo.com` |
| `ODOO_DB` | No | `riss-group-corzic-main-16227912` |
| `ODOO_USERNAME` | No | `justin.reyes@corzic.com` |
| `ODOO_PASSWORD` | Yes | none |
| `ODOO_DEV_URL` | For order import | staging Odoo URL |
| `ODOO_DEV_DB` | For order import | staging Odoo DB |
| `ODOO_DEV_USERNAME` | For order import | `justin.reyes@corzic.com` |
| `ODOO_DEV_PASSWORD` | For order import | none |
| `ARIBA_CLIENT_ID` | For order import | none |
| `ARIBA_CLIENT_SECRET` | For order import | none |
| `ARIBA_APPLICATION_KEY` | For order import | none |
| `ARIBA_REALM` | For order import | `AN11091553062` |
| `SUFS_OUTPUT_DIR` | No | `/app/output` in Docker |

## Run locally

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ODOO_PASSWORD="your-password"
flask --app app run --host 0.0.0.0 --port 8000
```

The original command-line export still works:

```sh
python sufs_catalog.py
```
