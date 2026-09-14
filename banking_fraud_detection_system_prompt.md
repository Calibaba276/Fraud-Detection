# AI Agent Prompt: Python-Based Banking Fraud Detection Platform

## Role

Act as a senior Python software engineer and machine-learning engineer with experience designing financial transaction monitoring and fraud detection systems.

Your responsibility is to plan, implement, test, and document a **banking transaction fraud detection platform**. The implementation should be production-minded while remaining practical to develop locally.

Work incrementally and explain important technical decisions as you go. When the specification leaves room for interpretation, choose a sensible approach, briefly document the assumption, and continue. Do not pause for clarification unless the decision would create a significant architectural consequence.

---

# 1. System Objective

Create a fraud-monitoring application capable of examining banking transactions and determining whether they appear suspicious.

The initial implementation should support:

1. Loading transaction records from CSV and Parquet files, while keeping the architecture suitable for future streaming ingestion.
2. Validating, cleaning, transforming, and enriching transaction/account information before it reaches the detection layer.
3. Combining two independent detection approaches:
   - A configurable deterministic rules system.
   - A supervised machine-learning fraud classifier.
4. Producing a normalized fraud probability/risk value between **0 and 1**, together with an operational action:
   - `approve`
   - `review`
   - `decline`
5. Providing a REST interface through which transactions can be scored.
6. Recording suspicious activity and generating alerts for transactions that exceed appropriate risk thresholds.
7. Providing a dedicated evaluation process that emphasizes metrics appropriate for highly imbalanced fraud datasets rather than relying primarily on accuracy.

The final system should be structured so that individual components can later be replaced or expanded without rewriting the entire application.

---

# 2. Required Technology

Use the following technologies unless there is a strong technical reason to make an alternative choice:

### Programming
- Python 3.11 or newer

### Data Processing
- pandas
- NumPy
- PyArrow

### Machine Learning
- scikit-learn
- XGBoost or LightGBM
- imbalanced-learn for techniques such as SMOTE, undersampling, or related imbalance-handling approaches

### API Layer
- FastAPI
- Pydantic

### Persistence
Design the database to make use of **PostgreSQL** for application.

### Experiment Management
Prefer MLflow for experiment/model tracking.

If MLflow cannot reasonably be used in the development environment, implement a simple local experiment-tracking mechanism instead.

### Testing
- pytest
- pytest-cov

### Project Management
- `pyproject.toml`
- Python virtual environment
- Explicitly pinned dependencies

---

# 3. Transaction Data

No real banking dataset is supplied initially.

Therefore, create a synthetic transaction generator that produces data resembling realistic banking activity.

The generated dataset should intentionally contain a small minority of fraudulent transactions, targeting approximately **0.5%–2% fraud prevalence**.

At minimum, include these fields:

- `transaction_id`
- `timestamp`
- `account_id`
- `card_id`
- `amount`
- `currency`
- `merchant_id`
- `merchant_category`
- `transaction_type`
- `location`
- `device_id`
- `ip_address`
- `account_age_days`
- `avg_monthly_spend`
- `is_foreign_transaction`
- `is_fraud`

You may introduce additional columns whenever they improve the realism or usefulness of the system.

The synthetic generator should model plausible legitimate and fraudulent behavior rather than simply assigning random fraud labels.

For example, fraudulent activity may exhibit patterns such as:

- unusually large purchases,
- bursts of transactions,
- unfamiliar devices,
- unusual locations,
- foreign activity,
- suspicious merchants,
- abnormal spending behavior.

Document how fraudulent and legitimate records are generated.

The data-generation component must be isolated from the rest of the system so that a real dataset can later replace it with minimal modification.

Potential future datasets include sources such as **IEEE-CIS Fraud Detection** or publicly available credit-card fraud datasets.

---

# 4. Data Processing Pipeline

Build the application around a clear processing pipeline:

```text
Raw Transaction
      ↓
Ingestion
      ↓
Validation
      ↓
Cleaning
      ↓
Feature Construction
      ↓
Rules Engine ──────┐
                   ├──→ Risk Aggregation → Decision
ML Model ──────────┘
```

The pipeline should be modular and testable.

## 4.1 Ingestion

Implement readers capable of loading:

- CSV files

Validate incoming records against appropriate schemas.

Pydantic should be used where it provides meaningful schema validation, particularly around API input and transaction structures.

Handle common data-quality problems including:

- missing values,
- malformed timestamps,
- invalid numerical values,
- duplicate transactions,
- inconsistent data types,
- invalid categorical values.

Do not silently discard problematic records. Make the handling behavior explicit and observable.

---

# 5. Feature Engineering

Construct features that capture both the transaction itself and how it differs from the account's normal behavior.

At minimum, implement the following categories.

## 5.1 Transaction Velocity

Calculate recent activity for an account over multiple time horizons.

Examples include:

- transaction count during the previous hour,
- transaction count during the previous 24 hours,
- transaction count during the previous 7 days,
- transaction amount totals over equivalent windows.

Ensure that feature calculations do not accidentally use information from the future relative to the transaction being scored.

---

## 5.2 Spending Behavior

Compare the current transaction against the account's historical behavior.

Useful features include:

- difference from historical average transaction amount,
- ratio of current amount to normal spending,
- deviation from account-level spending statistics,
- abnormal transaction amount indicators.

Avoid data leakage when calculating these values.

---

## 5.3 Geographic Behavior

Create features capable of identifying suspicious movement between transactions.

For example, compare the location and timestamp of consecutive transactions belonging to an account.

The system should be able to identify situations where an account appears to have made transactions in geographically distant locations within a physically unrealistic amount of time.

---

## 5.4 Temporal Features

Extract time-related characteristics such as:

- hour,
- day of week,
- weekend indicator,
- nighttime indicator.

These should help the model recognize behavior occurring outside an account's typical activity patterns.

---

## 5.5 Merchant Risk

Calculate historical merchant or merchant-category risk where sufficient historical information exists.

Examples:

- historical fraud rate for a merchant,
- historical fraud rate for a merchant category,
- transaction frequency associated with the merchant.

Take care to prevent target leakage when constructing these statistics.

---

# 6. Rule-Based Detection

Implement a separate rules subsystem that can evaluate transactions independently from the ML model.

Rules must be:

- easy to understand,
- configurable,
- independently enabled or disabled,
- individually testable.

Store rule configuration in a human-readable format such as YAML or JSON.

The initial rule collection should include examples such as:

### Abnormal Amount
Flag transactions whose amount is significantly above the customer's normal spending behavior, such as exceeding a configurable number of standard deviations.

### Excessive Activity
Trigger when an account performs more than a configurable number of transactions during a configurable time interval.

### Blocklisted Entities
Detect transactions involving configured:

- merchants,
- devices,
- IP addresses.

### Impossible Travel
Flag transactions when an account appears to move between distant countries or locations faster than physically possible.

Do not hard-code thresholds throughout the Python codebase. Place appropriate configuration in the rules configuration file.

The rules engine should return structured information describing which rules fired and why.

---

# 7. Machine-Learning Detection

Develop a supervised classification model for predicting whether a transaction is fraudulent.

Start with a strong but understandable baseline, such as:

- Random Forest,
- Gradient Boosting,
- XGBoost,
- or LightGBM.

The architecture should make it possible to introduce more advanced approaches later, including anomaly detection or neural-network-based models.

Because fraud is highly imbalanced, do not optimize the project around raw classification accuracy.

Investigate appropriate methods for handling imbalance, including techniques available through `imbalanced-learn`.

The training pipeline should clearly separate:

- training data,
- validation data,
- test data.

Avoid leakage between these datasets.

Save the trained model in a reproducible manner and make model loading separate from model training.

---

# 8. Risk Scoring and Final Decision

Every evaluated transaction should ultimately produce something equivalent to:

```text
risk_score: 0.00 - 1.00
decision: approve | review | decline
```

Design the scoring architecture so that rule-based signals and ML predictions can be combined in a controlled manner.

The decision thresholds should be configurable rather than scattered throughout the source code.

For example, the system could use configurable risk ranges such as:

```text
Low risk    → APPROVE
Medium risk → REVIEW
High risk   → DECLINE
```

The exact thresholds should be selected based on the evaluation results and clearly documented rather than presented as universally correct values.

The response should also make it possible to understand why a transaction received its risk classification.

---

# 9. REST API

Create a FastAPI service exposing the fraud detection functionality.

The API should provide appropriate endpoints for:

- service health,
- transaction scoring,
- potentially batch scoring,
- useful model/system metadata where appropriate.

Use Pydantic models to validate API requests and responses.

A transaction submitted to the scoring endpoint should receive:

- its transaction identifier,
- fraud risk score,
- final decision,
- relevant rule violations/signals,
- useful model information where appropriate.

The system should target a local response time of approximately **200 milliseconds or less for an individual transaction**, excluding unusual external infrastructure delays.

Measure this rather than simply claiming that the requirement has been met.

---

# 10. Persistence and Logging

Use PostgreSQL for the initial implementation.

Store useful information such as:

- transactions,
- fraud predictions,
- rule matches,
- decisions,
- timestamps,
- alerts.

Organize the database layer so that PostgreSQL.

Implement structured logging throughout important parts of the pipeline.

High-risk transactions should produce an alert or clearly identifiable log event.

---

# 11. Model Evaluation

Create a repeatable evaluation workflow specifically designed for fraud detection.

At minimum, report metrics such as:

- Precision
- Recall
- F1 score
- PR-AUC / Average Precision
- ROC-AUC
- confusion matrix

Give particular attention to **precision-recall performance**, since the positive class is intentionally rare.

Where useful, evaluate the system at different decision thresholds to show the trade-off between catching fraudulent transactions and generating false positives.

Never invent or estimate performance numbers without actually running the evaluation.

Report the real metrics produced by the trained model.

---

# 12. Testing Requirements

Create a meaningful automated test suite using pytest.

Test individual components as well as their interactions.

Tests should cover areas including:

- transaction validation,
- data cleaning,
- feature calculations,
- rolling/velocity features,
- geographic anomaly calculations,
- individual rules,
- rule configuration,
- model prediction,
- risk-score generation,
- decision thresholds,
- API validation,
- API responses,
- database operations where applicable.

Include an end-to-end test that demonstrates that synthetic transaction data can travel through the major stages of the application without failure.

Use pytest-cov to measure test coverage.

Do not optimize for an arbitrary coverage percentage at the expense of meaningful tests.

---

# 13. Project Quality Requirements

The implementation should satisfy the following conditions:

- The complete synthetic-data pipeline executes successfully.
- The ML model produces a measurable fraud-detection result.
- PR-AUC and other relevant fraud metrics are calculated from actual test results.
- No evaluation metrics are fabricated.
- The API can score an individual transaction successfully.
- Local transaction scoring should target roughly 200 ms or less.
- Rules can be modified without rewriting the core detection logic.
- Components are separated into sensible modules.
- Tests execute successfully.
- Important functionality has useful automated coverage.
- Documentation explains both how the system works and why important design choices were made.

---

# 14. Documentation

Produce a developer-friendly README that allows someone unfamiliar with the repository to get the project running in approximately **15 minutes or less**.

The README should cover:

1. What the project does.
2. System architecture.
3. Project directory structure.
4. Python/environment setup.
5. Dependency installation.
6. Synthetic dataset generation.
7. Model training.
8. Evaluation.
9. Starting the FastAPI server.
10. Example API requests.
11. Running tests.
12. Configuration of fraud rules.
13. Explanation of risk decisions.
14. Known limitations.
15. How a real-world dataset could replace the synthetic dataset.
16. Possible future streaming architecture.

Include useful command examples wherever appropriate.

---

# 15. Development Approach

Build the system in logical stages rather than producing an unstructured collection of scripts.

## Self-Audit at Every Step

For every implementation step, review all code created or changed in that step before moving on. Check it for syntax errors, import and dependency issues, incorrect names or paths, type and schema mismatches, broken control flow, edge cases, and conflicts with the requirements in this prompt. Run the smallest relevant validation, test, lint, or command available to confirm the code works; fix every issue found before beginning the next step. Do not assume a component is correct merely because it was written—trace how it connects to the surrounding code and ensure it introduces no errors.

A recommended sequence is:

### Stage 1 — Project Foundation
Create the repository structure, environment configuration, dependency management, and basic application skeleton.

### Stage 2 — Synthetic Data
Build and validate the transaction generator.

### Stage 3 — Data Pipeline
Implement ingestion, validation, cleaning, and feature engineering.

### Stage 4 — Rules Engine
Implement configurable fraud rules and their tests.

### Stage 5 — ML Pipeline
Train, evaluate, serialize, and load the fraud model.

### Stage 6 — Risk Engine
Combine ML predictions and deterministic signals into the final risk score and decision.

### Stage 7 — API
Expose the detection service through FastAPI.

### Stage 8 — Testing
Build the unit, integration, and end-to-end test suite.

### Stage 9 — Documentation & Performance
Complete the README, benchmark transaction-scoring latency, and perform a final system review.

At each stage, keep the code runnable and avoid introducing unnecessary complexity before it is needed.

---

# 16. Future-Proofing

Although the first version will operate on files, design the application around replaceable components.

The architecture should eventually allow:

```text
CSV / Parquet
      ↓
Batch Ingestion
      ↓
                    ┌── Rules
Transaction Stream ─┼── ML Model
                    └── Risk Engine
                          ↓
                    Decision / Alert
                          ↓
                Database / Monitoring
```

A future implementation should be able to replace batch file ingestion with Kafka or Redis Streams without rebuilding the fraud-detection logic.

Likewise, use PostgreSQL, and the initial ML classifier should be replaceable with a more sophisticated model.

---

# 17. Final Deliverable

The completed repository should contain a functioning, tested fraud detection application rather than only an architectural proposal.

It should demonstrate the complete flow:

```text
Generate / Load Data
        ↓
Validate & Clean
        ↓
Engineer Features
        ↓
Evaluate Rules
        ↓
Run ML Model
        ↓
Combine Risk Signals
        ↓
Generate 0–1 Risk Score
        ↓
Approve / Review / Decline
        ↓
Store & Log Result
        ↓
Expose Result Through API
```

Before declaring the project complete, actually execute the relevant pipeline, run the tests, evaluate the model, and verify the API.

Provide the **real measured evaluation results**, test results, and API latency rather than theoretical claims.

The finished system should be understandable to another Python developer, straightforward to extend, and structured as a realistic foundation for eventually processing real banking transactions.
