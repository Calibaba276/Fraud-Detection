# Put Sentinel online

The frontend and Python model run as two services. Scoring always calls your FastAPI backend. Until it is deployed and connected, the online dashboard shows a connection prompt and cannot score transactions.

## Python backend on Render

1. Push this repository, including `render.yaml`, to a GitHub repository you own. Keep generated data, artifacts, databases, and secrets out of Git.
2. Sign in to [Render](https://dashboard.render.com/), choose **New → Blueprint**, and connect that repository.
3. Review the blueprint: one **Free** Python web service. Set `FRAUD_ALLOWED_ORIGINS` to your frontend's exact origin, including `https://` with no trailing slash. Multiple origins can be comma-separated.
4. Create the service. The build installs dependencies, generates synthetic training data, and trains the model. Wait for deployment and check that `/ready` returns `{"status":"ready"}`.
5. Copy the service's HTTPS URL. In Render's environment settings, reveal the generated `FRAUD_API_KEY` privately.
6. Open Sentinel, choose **Connect engine**, enter that URL and API key, and connect. The key stays in page memory; enter it again after a reload.

The configuration follows Render's [FastAPI guide](https://render.com/docs/deploy-fastapi) and [Blueprint reference](https://render.com/docs/blueprint-spec). Python 3.13 is pinned to match the project's package wheels.

## Demo hosting limits

The blueprint uses SQLite in `/tmp`. History survives page refreshes but is erased when the free service restarts, redeploys, or sleeps. Free Render services sleep after 15 idle minutes and can take around a minute to wake. Export results before leaving a demo. See [Render's free-service limits](https://render.com/docs/free).

For durable history, configure `DATABASE_URL` with a supported database and install its driver. The API-key/account-header flow is for a research demonstration, not production user authentication. The payment authorizer is a development boundary, not a bank integration.

## Local demonstration

Follow README.md to start the backend at `http://127.0.0.1:8000` and frontend at `http://localhost:3000`. The local frontend selects that backend automatically. The hosted HTTPS dashboard requires an HTTPS backend; it cannot use your laptop's HTTP service.

## Troubleshooting

- **Access denied:** check the API key matches `FRAUD_API_KEY` exactly.
- **Cannot reach engine:** check the backend URL, `/ready`, and `FRAUD_ALLOWED_ORIGINS`. The origin must match the dashboard address you opened.
- **Model unavailable:** inspect training build logs and `FRAUD_MODEL_PATH`.
- **Timeout:** allow the service to wake; refresh history before submitting again. A timed-out request may already have been scored, and duplicate IDs are rejected.
- **Verification:** enter the transaction's account ID. Confirming keeps the payment held for manual review; denying blocks it. There is no final manual-release endpoint in this project.
