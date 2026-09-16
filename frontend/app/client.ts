export type Transaction = {
  transaction_id: string; timestamp: string; account_id: string; card_id: string;
  amount: number; currency: string; merchant_id: string; merchant_category: string;
  transaction_type: string; location: string; device_id: string; ip_address: string;
  account_age_days: number; avg_monthly_spend: number; is_foreign_transaction: boolean;
};
export type Score = {
  transaction_id: string; risk_score: number; decision: 'approve' | 'review' | 'decline';
  rule_matches: { rule_id: string; reason: string; severity: number }[];
  model_probability: number; model_version: string; processing_ms: number;
  workflow_status: 'approved' | 'pending_verification' | 'blocked' | 'verification_received';
  next_action: string; user_message: string; authorization_status: string;
};
export type RecordRow = { transaction: Transaction; result: Score };
export type SystemInfo = { model_name: string; model_version: string; feature_count: number; review_threshold: number; decline_threshold: number; model_weight: number; rule_weight: number; persistence: string; rules: { id: string; enabled: boolean }[] };
export type Connection = { url: string; key: string };
export const statuses = { approved: 'Approved', pending_verification: 'Needs verification', verification_received: 'Manual review', blocked: 'Blocked' };
export const ruleNames: { [key: string]: string } = { abnormal_amount: 'Unusual spending', excessive_activity: 'Transaction velocity', blocklists: 'Blocked entities', blocklist: 'Blocked entity', impossible_travel: 'Impossible travel' };
export const percent = (value: number) => (value * 100).toFixed(1) + '%';
export const humanize = (value: string) => value.replaceAll('_', ' ');
export const money = (amount: number, currency: string) => {
  try { return new Intl.NumberFormat('en', { style: 'currency', currency, maximumFractionDigits: 2 }).format(amount); }
  catch { return currency + ' ' + amount.toFixed(2); }
};
export const date = (value: string) => new Date(value).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
export function sample(foreign = false): Transaction {
  const now = new Date();
  return { transaction_id: 'txn_' + crypto.randomUUID(), timestamp: new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 19), account_id: 'acct_demo_1001', card_id: 'card_demo_42', amount: foreign ? 9000 : 75, currency: 'USD', merchant_id: foreign ? 'merchant_online_204' : 'merchant_grocery_101', merchant_category: foreign ? 'online' : 'grocery', transaction_type: 'purchase', location: foreign ? 'GB' : 'US', device_id: foreign ? 'device_new_72' : 'device_demo_10', ip_address: foreign ? '192.0.2.72' : '192.0.2.10', account_age_days: foreign ? 30 : 730, avg_monthly_spend: 1500, is_foreign_transaction: foreign };
}
export async function request<T>(connection: Connection, path: string, method = 'GET', body?: unknown, account?: string): Promise<T> {
  if (!connection.url) throw new Error('Connect your detection engine to start analyzing transactions.');
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 75000);
  try {
    const headers: { [key: string]: string } = {};
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (connection.key) headers['X-API-Key'] = connection.key;
    if (account) headers['X-Account-ID'] = account;
    const response = await fetch(connection.url + path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body), signal: controller.signal, cache: 'no-store', credentials: 'omit' });
    const data = await response.json().catch(() => null) as { detail?: string | { loc: string[]; msg: string }[] } | null;
    if (!response.ok) {
      if (response.status === 401) throw new Error('Access denied. Check the API key in Connection settings.');
      if (response.status === 503) throw new Error(typeof data?.detail === 'string' ? data.detail : 'The detection model is not ready. Train the model or wait for the service to start.');
      const detail = Array.isArray(data?.detail) ? data.detail.map((item: { loc: string[]; msg: string }) => item.loc.slice(1).join('.') + ': ' + item.msg).join('; ') : data?.detail;
      throw new Error(detail || 'The detection service returned an error (' + response.status + ').');
    }
    if (data === null || typeof data !== 'object') throw new Error('The service returned an unexpected response. Check the backend URL and retry after the service wakes up.');
    return data as T;
  } catch (error) {
    if (error instanceof TypeError) throw new Error('Could not reach the detection engine. Check the service URL and that this dashboard is allowed to connect.');
    if (error instanceof Error && error.name === 'AbortError') throw new Error('The service took too long to respond. It may be waking up; wait and retry. Refresh history before resubmitting a transaction.');
    throw error;
  } finally { clearTimeout(timer); }
}
export function exportCsv(rows: RecordRow[]) {
  const fields = ['transaction_id', 'timestamp', 'account_id', 'amount', 'currency', 'merchant_id', 'merchant_category', 'risk_score', 'decision', 'workflow_status', 'authorization_status', 'model_probability', 'rule_reasons'];
  const escape = (value: unknown) => { let text = String(value ?? ''); if (/^[=+\-@\t\r\n]/.test(text)) text = "'" + text; return '"' + text.replaceAll('"', '""') + '"'; };
  const lines = rows.map(({ transaction: t, result: r }) => [t.transaction_id, t.timestamp, t.account_id, t.amount, t.currency, t.merchant_id, t.merchant_category, r.risk_score, r.decision, r.workflow_status, r.authorization_status, r.model_probability, r.rule_matches.map(match => match.reason).join('; ')].map(escape).join(','));
  const url = URL.createObjectURL(new Blob(['\uFEFF' + [fields.join(','), ...lines].join('\r\n')], { type: 'text/csv;charset=utf-8;' }));
  const link = document.createElement('a'); link.href = url; link.download = 'sentinel-transactions.csv'; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}

