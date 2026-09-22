'use client';

import type { FormEvent } from 'react';
import { Badge } from './components';
import { sample, percent, money, date, humanize, ruleNames, type RecordRow, type Transaction } from './client';

type FormProps = {
  form: Transaction;
  setForm: (value: Transaction) => void;
  busy: boolean;
  connected: boolean;
  error: string;
  onSubmit: (event: FormEvent) => void;
  onClose: () => void;
  onConnect: () => void;
};

export function TransactionForm({
  form,
  setForm,
  busy,
  connected,
  error,
  onSubmit,
  onClose,
  onConnect,
}: FormProps) {
  function field<K extends keyof Transaction>(key: K, value: Transaction[K]) {
    setForm({ ...form, [key]: value });
  }

  return (
    <form onSubmit={onSubmit} className="modal-body">
      <div className="sample-bar">
        <span>Try synthetic data</span>
        <button type="button" className="button secondary" disabled={busy} onClick={() => setForm(sample())}>
          Everyday purchase
        </button>
        <button type="button" className="button secondary" disabled={busy} onClick={() => setForm(sample(true))}>
          Unusual purchase
        </button>
      </div>
      <p className="form-hint">Examples fill the form only. Your model determines the outcome when you select Analyze.</p>

      <fieldset disabled={busy}>
        <legend>
          01 <span>Transaction details</span>
        </legend>
        <div className="form-grid">
          <label className="field full">
            Transaction ID
            <input required value={form.transaction_id} onChange={event => field('transaction_id', event.target.value)} />
          </label>
          <label className="field">
            Amount
            <input
              required
              type="number"
              min="0.01"
              step="0.01"
              value={form.amount}
              onChange={event => field('amount', Number(event.target.value))}
            />
          </label>
          <label className="field">
            Currency
            <input
              required
              maxLength={3}
              minLength={3}
              pattern="[A-Za-z]{3}"
              value={form.currency}
              onChange={event => field('currency', event.target.value.toUpperCase())}
            />
          </label>
          <label className="field">
            Date and time <span className="optional">local time</span>
            <input
              required
              type="datetime-local"
              step="1"
              value={form.timestamp}
              onChange={event => field('timestamp', event.target.value)}
            />
          </label>
          <label className="field">
            Transaction type
            <select value={form.transaction_type} onChange={event => field('transaction_type', event.target.value)}>
              {['purchase', 'transfer', 'withdrawal'].map(value => (
                <option key={value}>{value}</option>
              ))}
            </select>
          </label>
          <label className="field">
            Merchant ID
            <input required value={form.merchant_id} onChange={event => field('merchant_id', event.target.value)} />
          </label>
          <label className="field">
            Merchant category
            <select value={form.merchant_category} onChange={event => field('merchant_category', event.target.value)}>
              {['grocery', 'electronics', 'travel', 'fuel', 'online', 'restaurant', 'cash'].map(value => (
                <option key={value}>{value}</option>
              ))}
            </select>
          </label>
        </div>
      </fieldset>

      <fieldset disabled={busy}>
        <legend>
          02 <span>Account &amp; spending</span>
        </legend>
        <div className="form-grid">
          <label className="field">
            Account ID
            <input required value={form.account_id} onChange={event => field('account_id', event.target.value)} />
          </label>
          <label className="field">
            Card reference ID
            <input required value={form.card_id} onChange={event => field('card_id', event.target.value)} />
            <small>Use a reference ID, not a full card number.</small>
          </label>
          <label className="field">
            Account age in days
            <input
              required
              type="number"
              min="0"
              step="1"
              value={form.account_age_days}
              onChange={event => field('account_age_days', Number(event.target.value))}
            />
          </label>
          <label className="field">
            Average monthly spend
            <input
              required
              type="number"
              min="0"
              step="0.01"
              value={form.avg_monthly_spend}
              onChange={event => field('avg_monthly_spend', Number(event.target.value))}
            />
            <small>In the same currency as the transaction.</small>
          </label>
        </div>
      </fieldset>

      <fieldset disabled={busy}>
        <legend>
          03 <span>Device &amp; location</span>
        </legend>
        <div className="form-grid">
          <label className="field">
            Device ID
            <input required value={form.device_id} onChange={event => field('device_id', event.target.value)} />
          </label>
          <label className="field">
            IP address
            <input required value={form.ip_address} onChange={event => field('ip_address', event.target.value)} />
          </label>
          <label className="field">
            Country / location
            <input required value={form.location} onChange={event => field('location', event.target.value.toUpperCase())} />
          </label>
          <label className="checkbox-field">
            <input
              type="checkbox"
              checked={form.is_foreign_transaction}
              onChange={event => field('is_foreign_transaction', event.target.checked)}
            />
            <span>
              Foreign transaction
              <small>Activity outside the account&rsquo;s home country</small>
            </span>
          </label>
        </div>
      </fieldset>

      {error && (
        <div className="message error" role="alert">
          {error}
        </div>
      )}

      {!connected && (
        <div className="message setup">
          Connect the detection engine before submitting.
          <button className="text-button" type="button" onClick={onConnect}>
            Connection settings ↗
          </button>
        </div>
      )}

      <div className="modal-actions">
        <span className="muted">Scored by your Python model + rules</span>
        <button type="button" className="button secondary" disabled={busy} onClick={onClose}>
          Cancel
        </button>
        <button type="submit" className="button primary" disabled={busy || !connected}>
          {busy ? 'Analyzing…' : '◎ Analyze transaction'}
        </button>
      </div>
    </form>
  );
}

type ResultProps = {
  row: RecordRow;
  busy: boolean;
  account: string;
  setAccount: (value: string) => void;
  verify: (confirmed: boolean) => Promise<void>;
  onClose: () => void;
  error: string;
  notice: string;
};

export function ResultDetails({ row, busy, account, setAccount, verify, onClose, error, notice }: ResultProps) {
  const { transaction, result } = row;

  return (
    <div className="modal-body">
      <div className={'result-hero ' + result.decision}>
        <div>
          <p className="eyebrow">COMBINED RISK SCORE</p>
          <strong>
            {percent(result.risk_score)}
            <small> / 100%</small>
          </strong>
          <span className="muted">Model + strongest rule signal</span>
        </div>
        <div>
          <Badge status={result.workflow_status} />
          <p className="result-decision">
            Model decision: <b>{humanize(result.decision)}</b>
          </p>
        </div>
      </div>

      <div className="info-note">
        <b>{humanize(result.next_action === 'none' ? 'No further action required' : result.next_action)}</b>
        <p>{result.user_message}</p>
      </div>

      <dl className="detail-grid">
        <div>
          <dt>Amount</dt>
          <dd>{money(transaction.amount, transaction.currency)}</dd>
        </div>
        <div>
          <dt>Account</dt>
          <dd>{transaction.account_id}</dd>
        </div>
        <div>
          <dt>Merchant</dt>
          <dd>{transaction.merchant_id}</dd>
        </div>
        <div>
          <dt>Time</dt>
          <dd>{date(transaction.timestamp)}</dd>
        </div>
        <div>
          <dt>Model probability</dt>
          <dd>{percent(result.model_probability)}</dd>
        </div>
        <div>
          <dt>Payment status</dt>
          <dd>{humanize(result.authorization_status)}</dd>
        </div>
        <div>
          <dt>Model version</dt>
          <dd>{result.model_version}</dd>
        </div>
        <div>
          <dt>Processing time</dt>
          <dd>{result.processing_ms.toFixed(1)} ms</dd>
        </div>
      </dl>

      <h3 className="section-title">
        Detection signals <span className="tag">{result.rule_matches.length} rules matched</span>
      </h3>

      {result.rule_matches.length ? (
        result.rule_matches.map(match => (
          <div className="rule-match" key={match.rule_id}>
            <div>
              <b>{ruleNames[match.rule_id] || humanize(match.rule_id)}</b>
              <p>{match.reason}</p>
            </div>
            <span className="tag">{percent(match.severity)} severity</span>
          </div>
        ))
      ) : (
        <div className="quiet-note">
          No configured rules were triggered. The model may still identify risk from the transaction&rsquo;s features.
        </div>
      )}

      {result.workflow_status === 'pending_verification' && (
        <div className="verification-box">
          <h3>Account-holder verification</h3>
          <p>
            Record whether the account holder recognizes this transaction. Confirmation keeps the
            payment on hold for manual review.
          </p>
          <label className="field">
            Account ID for this confirmation
            <input
              autoComplete="off"
              value={account}
              onChange={event => setAccount(event.target.value)}
              placeholder="Enter the transaction's account ID"
              disabled={busy}
            />
          </label>
          <div className="button-row">
            <button className="button danger" disabled={!account.trim() || busy} onClick={() => void verify(false)}>
              {busy ? 'Submitting…' : 'Not recognized · block'}
            </button>
            <button className="button primary" disabled={!account.trim() || busy} onClick={() => void verify(true)}>
              {busy ? 'Submitting…' : 'Recognized · confirm'}
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="message error" role="alert">
          {error}
        </div>
      )}
      {notice && (
        <div className="message success" role="status">
          {notice}
        </div>
      )}

      <div className="modal-actions">
        <span className="muted">Research model · Scores are estimates</span>
        <button className="button secondary" disabled={busy} onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
}
