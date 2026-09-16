'use client';
import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';
import { Badge, Engine, Modal } from './components';
import { TransactionForm, ResultDetails } from './transaction-panels';
import { request, sample, statuses, percent, money, date, humanize, exportCsv, type Connection, type RecordRow, type Score, type Transaction, type SystemInfo } from './client';

type View = 'Overview' | 'Transactions' | 'Review queue' | 'Detection engine';
const views: View[] = ['Overview', 'Transactions', 'Review queue', 'Detection engine'];
const symbols = ['▦', '⇄', '◎', '◇'];
const headings = {
  Overview: ['Every transaction. A clearer picture.', 'Monitor activity, investigate risk, and make informed decisions.'],
  Transactions: ['Follow the money. Understand the risk.', 'Search your analyzed transactions and inspect the signals behind each decision.'],
  'Review queue': ['The transactions that need a closer look.', 'Collect account-holder verification and follow transactions awaiting manual review.'],
  'Detection engine': ['See what powers the decision.', 'Understand how your trained model and configured rules work together.'],
};
export default function Dashboard() {
  const [view, setView] = useState<View>('Overview');
  const [connection, setConnection] = useState<Connection>({ url: '', key: '' });
  const [draftUrl, setDraftUrl] = useState('');
  const [draftKey, setDraftKey] = useState('');
  const [connected, setConnected] = useState(false);
  const [records, setRecords] = useState<RecordRow[]>([]);
  const [system, setSystem] = useState<SystemInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [dialog, setDialog] = useState<'connection' | 'analyze' | 'result' | null>(null);
  const [form, setForm] = useState<Transaction | null>(null);
  const [selected, setSelected] = useState<RecordRow | null>(null);
  const [account, setAccount] = useState('');
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [updated, setUpdated] = useState('');
  const refreshVersion = useRef(0);
  const refresh = useCallback(async () => {
    if (!connection.url) return;
    const version = ++refreshVersion.current;
    setLoading(true); setError('');
    try {
      const [info, rows] = await Promise.all([request<SystemInfo>(connection, '/system'), request<RecordRow[]>(connection, '/transactions?limit=500')]);
      if (version !== refreshVersion.current) return;
      if (!Array.isArray(rows) || !info || typeof info.model_version !== 'string' || rows.some(row => !row?.transaction?.transaction_id || !row?.result || !(row.result.workflow_status in statuses))) throw new Error('The service response does not match the fraud detection API. Check your backend URL.');
      setSystem(info); setRecords(rows); setConnected(true); setUpdated(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    } catch (err) { if (version === refreshVersion.current) { setConnected(false); setError((err as Error).message); } }
    finally { if (version === refreshVersion.current) setLoading(false); }
  }, [connection]);
  useEffect(() => {
    let url = '';
    try { url = localStorage.getItem('sentinel.backendUrl') || ''; } catch {}
    if (!url && ['localhost', '127.0.0.1'].includes(window.location.hostname)) url = 'http://127.0.0.1:8000';
    setDraftUrl(url);
    if (url) setConnection({ url, key: '' });
  }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  function navigate(next: View) { setView(next); setFilter('all'); setQuery(''); setPage(1); }
  function openAnalyze() { setForm(sample()); setError(''); setNotice(''); setDialog('analyze'); }
  function openRecord(row: RecordRow) { setSelected(row); setAccount(''); setError(''); setNotice(''); setDialog('result'); }
  function openConnection() { setError(''); setDialog('connection'); }
  function closeDialog() { if (!busy) setDialog(null); }
  function connect(event: FormEvent) {
    event.preventDefault();
    try {
      const parsed = new URL(draftUrl);
      if (!['http:', 'https:'].includes(parsed.protocol) || parsed.username || parsed.password || parsed.search || parsed.hash) throw new Error('Use an HTTP or HTTPS service URL without credentials, a query, or a fragment.');
      if (window.location.protocol === 'https:' && parsed.protocol !== 'https:') throw new Error('The online dashboard needs an HTTPS backend URL.');
      const url = parsed.href.replace(/\/+$/, '');
      try { localStorage.setItem('sentinel.backendUrl', url); } catch {}
      ++refreshVersion.current;
      setRecords([]); setSelected(null); setSystem(null); setUpdated(''); setConnected(false); setError('');
      setConnection({ url, key: draftKey.trim() }); setDialog(null);
    } catch (err) { setError((err as Error).message || 'Enter a valid backend URL.'); }
  }
  async function analyze(event: FormEvent) {
    event.preventDefault();
    if (!form || busy) return;
    ++refreshVersion.current; setLoading(false);
    setBusy(true); setError('');
    try {
      const transaction: Transaction = { ...form, timestamp: new Date(form.timestamp).toISOString(), currency: form.currency.toUpperCase() };
      const result = await request<Score>(connection, '/score', 'POST', transaction);
      const row = { transaction, result };
      setRecords(previous => [row, ...previous.filter(item => item.transaction.transaction_id !== transaction.transaction_id)].slice(0, 500));
      setSelected(row); setAccount(''); setConnected(true); setDialog('result');
      setUpdated(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    } catch (err) { setError((err as Error).message); }
    finally { setBusy(false); }
  }
  async function verify(confirmed: boolean) {
    if (!selected || !account.trim() || busy) return;
    ++refreshVersion.current; setLoading(false);
    setBusy(true); setError(''); setNotice('');
    try {
      const result = await request<Score>(connection, '/transactions/' + encodeURIComponent(selected.transaction.transaction_id) + '/verify', 'POST', { confirmed }, account.trim());
      setSelected({ ...selected, result });
      setRecords(previous => previous.map(row => row.transaction.transaction_id === result.transaction_id ? { ...row, result } : row));
      setNotice(result.user_message);
    } catch (err) { setError((err as Error).message); }
    finally { setBusy(false); }
  }
  const approved = records.filter(row => row.result.workflow_status === 'approved').length;
  const pending = records.filter(row => row.result.workflow_status === 'pending_verification').length;
  const blocked = records.filter(row => row.result.workflow_status === 'blocked').length;
  const manual = records.filter(row => row.result.workflow_status === 'verification_received').length;
  const filtered = records.filter(row => {
    const status = row.result.workflow_status;
    if (view === 'Review queue' && !['pending_verification', 'verification_received'].includes(status)) return false;
    if (filter !== 'all' && status !== filter) return false;
    return [row.transaction.transaction_id, row.transaction.account_id, row.transaction.merchant_id, row.transaction.merchant_category].some(value => value.toLowerCase().includes(query.toLowerCase()));
  });
  const totalPages = Math.max(1, Math.ceil(filtered.length / 8));
  const currentPage = Math.min(page, totalPages);
  const visible = filtered.slice((currentPage - 1) * 8, currentPage * 8);
  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="/" aria-label="Sentinel home"><b className="brand-mark">S</b>Sentinel<span>.</span></a>
      <div className="workspace"><b>FD</b><div>Fraud detection<small>Research workspace</small></div></div>
      <p className="nav-label">WORKSPACE</p>
      <nav aria-label="Main navigation">{views.map((name, index) => <button key={name} className={'nav-item ' + (view === name ? 'active' : '')} aria-current={view === name ? 'page' : undefined} onClick={() => navigate(name)}><span aria-hidden="true">{symbols[index]}</span>{name}{name === 'Review queue' && pending + manual > 0 && <b className="nav-count">{pending + manual}</b>}</button>)}</nav>
      <div className="sidebar-bottom"><div className="side-note"><span className="status-dot"/>Built for closer inspection<p>Understand the risk behind every transaction.</p><button className="text-button" onClick={openConnection}>Connection settings ↗</button></div><div className="profile"><b className="avatar">RA</b><div>Research analyst<small>Demonstration workspace</small></div></div></div>
    </aside>
    <div className="main-shell">
      <header className="topbar"><div>Workspace <span className="slash">/</span><strong>{view}</strong></div><button className={'connection-status ' + (connected ? 'online' : '')} onClick={openConnection}><span className="status-dot"/>{loading ? 'Connecting…' : connected ? 'Engine connected' : 'Connect engine'} <span>⌄</span></button></header>
      <main>
        <div className="page-heading"><div><p className="eyebrow">YOUR MONITORING WORKSPACE</p><h1>{headings[view][0]}</h1><p>{headings[view][1]}</p></div><button className="button primary" onClick={openAnalyze}>＋ Analyze transaction</button></div>
        {error && !dialog && <div className="message error" role="alert">{error}<button className="text-button" onClick={openConnection}>Connection settings</button></div>}
        {notice && !dialog && <div className="message success" role="status">{notice}<button className="icon-button" aria-label="Dismiss notification" onClick={() => setNotice('')}>×</button></div>}
        {!connected && !loading && !error && <div className="message setup"><div><strong>Connect your detection engine</strong><p>Your workspace is ready. Connect the Python service to analyze transactions and see results here.</p></div><button className="button secondary" onClick={openConnection}>Set up connection ↗</button></div>}
        {view === 'Overview' && <><div className="intro-banner"><div className="intro-symbol" aria-hidden="true">◎</div><div><h2>Your first line of insight.</h2><p>Machine learning and configurable rules, working together to surface suspicious activity.</p></div><span className="tag">Model + rules</span></div><div className="stats-grid">{[
          ['Transactions analyzed', records.length, 'Latest 500 scored transactions', '⇄'],
          ['Approved', approved, 'Authorized by the detection engine', '✓'],
          ['Awaiting verification', pending, 'On hold for account-holder response', '◷'],
          ['Blocked', blocked, 'Declined or denied by account holder', '⊘'],
        ].map(([title, count, caption, icon], index) => <article className="stat-card" key={title}><span className="stat-label">{title}<span className={'stat-icon tone-' + index} aria-hidden="true">{icon}</span></span><strong>{system ? count : '—'}</strong><small>{caption}</small></article>)}</div></>}
        {view === 'Detection engine' ? <Engine system={system}/> : <section className="panel">
          <div className="panel-heading"><div><h2>{view === 'Review queue' ? 'Review queue' : 'Transaction activity'}</h2><p>{view === 'Review queue' ? pending + ' awaiting verification · ' + manual + ' awaiting manual review' : 'A live view of the transactions you analyze.'}</p></div><div className="button-row"><button className="button subtle" disabled={loading || !connection.url || busy} onClick={() => void refresh()}>{loading ? 'Refreshing…' : '↻ Refresh'}</button><button className="button secondary" disabled={!filtered.length} onClick={() => { exportCsv(filtered); setNotice('Exported ' + filtered.length + ' transactions.'); }}>↓ Export CSV</button></div></div>
          <div className="table-toolbar"><label className="search-field"><span aria-hidden="true">⌕</span><input aria-label="Search transactions" placeholder="Search transaction, account, or merchant…" value={query} onChange={event => { setQuery(event.target.value); setPage(1); }}/></label><select aria-label="Filter by workflow status" value={filter} onChange={event => { setFilter(event.target.value); setPage(1); }}><option value="all">All statuses</option>{Object.entries(statuses).filter(([key]) => view !== 'Review queue' || ['pending_verification', 'verification_received'].includes(key)).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>
          {visible.length ? <><div className="table-scroll"><table><thead><tr><th>Transaction</th><th>Merchant</th><th>Amount</th><th>Risk score</th><th>Status</th><th><span className="sr-only">Details</span></th></tr></thead><tbody>{visible.map(row => <tr key={row.transaction.transaction_id}><td><button className="transaction-link" onClick={() => openRecord(row)}>{row.transaction.transaction_id}</button><small>{row.transaction.account_id} · {date(row.transaction.timestamp)}</small></td><td><span className="merchant-name">{humanize(row.transaction.merchant_category)}</span><small>{row.transaction.merchant_id}</small></td><td className="amount-cell">{money(row.transaction.amount, row.transaction.currency)}<small>{row.transaction.currency}</small></td><td><div className={'risk-cell ' + row.result.decision}><span>{percent(row.result.risk_score)}</span><div className="risk-track"><i style={{ width: percent(row.result.risk_score) }}/></div></div></td><td><Badge status={row.result.workflow_status}/></td><td><button className="icon-button" aria-label={'View transaction ' + row.transaction.transaction_id} onClick={() => openRecord(row)}>↗</button></td></tr>)}</tbody></table></div><div className="table-footer"><span>Showing {(currentPage - 1) * 8 + 1}–{Math.min(currentPage * 8, filtered.length)} of {filtered.length} transactions{updated && ' · Updated ' + updated}{!connected && ' · Last loaded data'}</span><div className="pagination"><button aria-label="Previous page" disabled={currentPage === 1} onClick={() => setPage(currentPage - 1)}>‹</button><span>{currentPage} / {totalPages}</span><button aria-label="Next page" disabled={currentPage >= totalPages} onClick={() => setPage(currentPage + 1)}>›</button></div></div></> : <div className="empty-state"><div className="empty-icon" aria-hidden="true">{view === 'Review queue' ? '✓' : '⇄'}</div><h3>{query || filter !== 'all' ? 'No matching transactions.' : view === 'Review queue' ? 'Nothing waiting for review.' : 'Good decisions start with a closer look.'}</h3><p>{query || filter !== 'all' ? 'Try a different search or status filter.' : view === 'Review queue' ? 'Transactions placed on hold will appear here for verification.' : <>Analyze your first transaction to see its risk score,<br/>detection signals, and recommended next action.</>}</p>{view !== 'Review queue' && <button className="button secondary" onClick={openAnalyze}>＋ Analyze your first transaction</button>}</div>}
        </section>}
        <footer>Sentinel · Banking fraud detection<span>Research workspace · Synthetic data recommended</span></footer>
      </main>
    </div>
    {dialog === 'connection' && <Modal title="Connect your detection engine" subtitle="Use your local Python service or its hosted HTTPS address." onClose={closeDialog}><form onSubmit={connect} className="modal-body"><label className="field">Backend URL<input required type="url" placeholder="https://your-service.onrender.com" value={draftUrl} onChange={event => setDraftUrl(event.target.value)}/></label><label className="field">API key <span className="optional">if configured on your service</span><input type="password" autoComplete="off" placeholder="Enter your service API key" value={draftKey} onChange={event => setDraftKey(event.target.value)}/></label><p className="muted">Your API key is kept in memory for this page session. It is never saved to browser storage.</p><div className="info-note"><b>Running on your laptop?</b><p>Start the Python service, then use <code>http://127.0.0.1:8000</code>. For the online dashboard, deploy the supplied hosting configuration and enter its HTTPS URL here.</p><p>The backend must allow this dashboard’s origin in its connection settings. A sleeping host may take a minute to wake.</p></div>{error && <div className="message error" role="alert">{error}</div>}<div className="modal-actions"><button type="button" className="button secondary" onClick={closeDialog}>Cancel</button><button className="button primary" type="submit">Connect engine ↗</button></div></form></Modal>}
    {dialog === 'analyze' && form && <Modal title="Analyze a transaction" subtitle="Submit transaction details to your trained fraud detection model." onClose={closeDialog} wide><TransactionForm form={form} setForm={setForm} busy={busy} connected={connected} error={error} onSubmit={analyze} onClose={closeDialog} onConnect={openConnection}/></Modal>}
    {dialog === 'result' && selected && <Modal title="Transaction analysis" subtitle={selected.transaction.transaction_id} onClose={closeDialog} wide><ResultDetails row={selected} busy={busy} account={account} setAccount={setAccount} verify={verify} onClose={closeDialog} error={error} notice={notice}/></Modal>}
  </div>;
}
