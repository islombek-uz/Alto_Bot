# PythonAnywhere webhook deployment

This setup uses a Cloudflare Worker for both Telegram Bot API calls and the incoming Telegram webhook. PythonAnywhere serves the Flask app through WSGI; do not start an aiohttp server on port 8000.

## Cloudflare Worker

Deploy `cloudflare_worker.js` as a module Worker and configure these variables/secrets in the Worker settings:

- `WORKER_API_SECRET`: long random URL-safe value used to protect the API proxy routes.
- `TELEGRAM_WEBHOOK_PATH`: long random URL path segment.
- `TELEGRAM_WEBHOOK_SECRET`: random value containing only letters, digits, `_`, or `-`.
- `PA_WEBHOOK_URL`: `https://<account>.pythonanywhere.com/telegram-webhook`.
- `PA_WEBHOOK_SECRET`: long random value shared with the PythonAnywhere app as `WEBHOOK_AUTH_SECRET`.

The Worker forwards Telegram API requests and OpenRouter API requests. Requests and their authorization headers pass through Cloudflare, so use this only if that data path is acceptable to you.

## PythonAnywhere

Install packages from `requirements.txt`. In the PythonAnywhere Web tab, configure the WSGI file to import `application` from this project's `wsgi.py`; do not run `main.py` as a long-lived polling process.

Set these variables for the web app, or place them in a manually created server-side `.env` file:

- `BOT_TOKEN`
- `OPENAI_API_KEY`
- `ADMIN_ID` (optional; use `0` if unset)
- `WEBHOOK_AUTH_SECRET`: exactly the same value as Worker `PA_WEBHOOK_SECRET`.
- `TELEGRAM_API_BASE_URL`: `https://<worker-domain>/api/<WORKER_API_SECRET>`.
- `OPENROUTER_BASE_URL`: `https://<worker-domain>/openrouter/<WORKER_API_SECRET>/api/v1`.

The `.env` file is ignored by Git and must not be committed.

## Register Telegram webhook

On a trusted computer with this project and its Python dependencies, set these values in a local, ignored `.env` file:

- `BOT_TOKEN`
- `WORKER_URL`: the Worker origin, for example `https://<worker-name>.<account>.workers.dev`.
- `WORKER_API_SECRET`
- `TELEGRAM_WEBHOOK_PATH`
- `TELEGRAM_WEBHOOK_SECRET`

Run `python setup_webhook.py` once. The script calls Telegram through the Worker and registers the Worker webhook URL. Check the PythonAnywhere web app error log if Telegram receives updates but the bot does not answer.

Free-tier network rules and service quotas can change. Confirm that the PythonAnywhere account can reach the Worker domain and that Cloudflare Worker limits cover the bot's traffic. OpenRouter traffic also passes through the Worker in this configuration.
