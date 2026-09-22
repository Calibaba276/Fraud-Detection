# Banking Fraud Detection Platform

A local-first fraud-monitoring service that generates realistic synthetic transactions, constructs leakage-aware historical features, evaluates configurable rules, trains a supervised classifier, and exposes a FastAPI scoring endpoint.

## Sentinel frontend

The `frontend/` folder contains a responsive React/TypeScript dashboard: overview, searchable history, CSV export, transaction scoring, verification queue, and model/rule information. Examples are synthetic inputs scored by your actual model.

> Authentication is intentionally simulated with browser localStorage for demonstration purposes. It is not secure and must be replaced with a real authentication provider before production use.

Set up Python and train the model using Quickstart below. Then, with Node.js 22.13+ installed:

```powershell
cd frontend
npm install
cd ..
.\start.ps1
```

Open `http://localhost:3000`. The startup script runs both services with local SQLite history. Press Ctrl+C to stop. If PowerShell blocks the script, use `powershell -ExecutionPolicy Bypass -File .\start.ps1` for that invocation.

Alternatively, run the services in separate terminals:

```powershell
# Terminal 1, repository root
$env:DATABASE_URL = "sqlite:///fraud_detection.db"
.\.venv\Scripts\python.exe -m uvicorn fraud_detection.api:app --host 127.0.0.1 --port 8000

# Terminal 2, frontend folder
cd frontend
npm run dev -- --host 127.0.0.1 --port 3000
```

Select **Analyze transaction**, choose **Everyday purchase** or **Unusual purchase**, and submit. Open a result to inspect risk signals and payment status. For held transactions, enter the account ID and record whether the account holder recognizes the payment. Confirmation still requires manual review.

Statistics and exports cover the latest 500 scored transactions. Amounts remain in their original currency. The backend URL is a saved device preference; API keys and transaction details are not stored in browser storage.

For online deployment, follow [HOSTING.md](HOSTING.md). The [Render blueprint](render.yaml) prepares the Python backend; a hosting account and deployment are required before online scoring works.

Frontend checks: `npm run build` and `npm run lint` inside `frontend/`. Backend checks: `python -m pytest -q` at the repository root.

## Quickstart

Requires Python 3.11+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m fraud_detection.cli generate --output data/transactions.csv --rows 20000
python -m fraud_detection.cli train data/transactions.csv --output artifacts/model.joblib
pytest --cov=fraud_detection
uvicorn fraud_detection.api:app --reload
```

The API is available at `http://127.0.0.1:8000`; health is `GET /health`, scoring is `POST /score`, and user confirmation is submitted to `POST /transactions/{transaction_id}/verify` with `{"confirmed": true}` or `{"confirmed": false}`. A reviewed transaction remains on hold after confirmation until manual review; a declined transaction is blocked. The generated CSV can also be written as Parquet by using a `.parquet` output path.

Set `DATABASE_URL` to persist scores, transaction history, workflow state, and verification updates across restarts. Set `FRAUD_API_KEY` to protect API requests; verification also requires the authenticated account's `X-Account-ID` header. The built-in authorizer is an in-memory payment boundary for development. Production deployments should provide a `PaymentAuthorizer` integration that calls the payment processor to authorize, hold, or reject the actual payment.

## Architecture

`generator` and `ingestion` are replaceable batch adapters. `features` computes only prior activity for velocity features. `rules` loads `rules.yaml`, `model` trains and serializes a class-balanced HistGradientBoosting baseline, and `risk` combines independent signals into a bounded score. `service` coordinates scoring, while `persistence` uses SQLAlchemy and defaults to SQLite for zero-setup development. Set `DATABASE_URL` and pass a PostgreSQL SQLAlchemy URL through the service integration for deployment; install `.[postgres]` for the driver.

Fraud labels are intentionally rare (about 1.2%) and correlate with unusually high amounts, foreign activity, and suspicious merchant categories. This is a demonstration dataset, not a claim about real fraud behavior.

## Decisions and configuration

`rules.yaml` controls rule enablement, thresholds, blocklists, and `approve`/`review`/`decline` boundaries. Risk is `0.7 * model_probability + 0.3 * strongest_rule_severity`, clipped to `[0, 1]`. `approve` authorizes, `review` holds for user verification, and `decline` blocks at the payment boundary. These weights and thresholds are starting points and should be calibrated against business costs and validation results.

## Evaluation and limitations

Training prints actual precision, recall, F1, average precision (PR-AUC), ROC-AUC, and confusion matrix from a stratified holdout. Run it locally to obtain metrics for the current seed and dependency versions; no metrics are embedded here. A production system needs temporal splits, calibrated probabilities, authenticated API access, richer geospatial data, drift monitoring, human-review feedback, and PostgreSQL migrations. MLflow can be added via `pip install -e ".[mlflow]"` around the training command.

A real dataset can replace `generate_transactions` if it maps to the `Transaction` schema. Future Kafka or Redis Streams consumers should emit the same validated transaction objects into `FraudService`, leaving rules, model, and risk logic unchanged.
