# Banking Fraud Detection Platform

A local-first fraud-monitoring service that generates realistic synthetic transactions, constructs leakage-aware historical features, evaluates configurable rules, trains a supervised classifier, and exposes a FastAPI scoring endpoint.

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
