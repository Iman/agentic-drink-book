import React, { useEffect, useRef, useState } from 'react';
import { applyLanguage, initialLanguage, translations } from './i18n.js';

async function request(path, language, csrf, body) {
  const response = await fetch(`/api/${path}`, {
    method: 'POST', credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', 'X-Chat-Language': language, ...(csrf ? { 'X-CSRF-Token': csrf } : {}) },
    body: JSON.stringify(body ?? {}),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error('Request failed');
    error.code = data?.code || 'generic';
    error.status = response.status;
    throw error;
  }
  if (!data) throw new Error('Invalid response');
  return data;
}

export default function App() {
  const [language, setLanguage] = useState(initialLanguage);
  const t = translations[language];
  const starters = t.starters;
  const number = new Intl.NumberFormat(language, { useGrouping: false });
  const [session, setSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [connecting, setConnecting] = useState(true);
  const [error, setError] = useState('');
  const input = useRef(null);
  const end = useRef(null);
  const pending = useRef(false);

  async function connect() {
    setConnecting(true);
    setError('');
    try {
      const data = await request('session', language);
      setSession(data);
      setMessages(data.history.flatMap(turn => [
        { role: 'user', text: turn.user }, { role: 'assistant', text: turn.assistant },
      ]));
    } catch {
      setError('connection');
    } finally { setConnecting(false); }
  }

  useEffect(() => { connect(); }, []);
  useEffect(() => { applyLanguage(language); }, [language]);
  useEffect(() => { end.current?.scrollIntoView({ block: 'nearest' }); }, [messages, busy]);

  async function send(event) {
    event.preventDefault();
    if (!draft.trim() || !session || pending.current) return;
    pending.current = true;
    setBusy(true);
    setError('');
    const text = draft;
    setDraft('');
    setMessages(current => [...current, { role: 'user', text }]);
    try {
      const data = await request('chat', language, session.csrf, { message: text });
      setMessages(current => [...current, { role: 'assistant', text: data.reply, status: data.status }]);
    } catch (failure) {
      setMessages(current => current.slice(0, -1));
      setDraft(text);
      setError(failure.code || 'network');
      if (failure.status === 401) setSession(null);
    } finally {
      pending.current = false;
      setBusy(false);
      requestAnimationFrame(() => input.current?.focus());
    }
  }

  async function reset() {
    if (!session || pending.current) return;
    pending.current = true;
    setBusy(true);
    setError('');
    try {
      const data = await request('reset', language, session.csrf);
      setSession(data);
      setMessages([]);
      setDraft('');
    } catch (failure) {
      setError(failure.code || 'network');
      if (failure.status === 401) setSession(null);
    } finally { pending.current = false; setBusy(false); }
  }

  function choose(text) {
    setDraft(text);
    input.current?.focus();
  }

  return <div className="app-shell" lang={language} dir={t.dir}>
    <aside className="sidebar">
      <a className="brand" href="/" aria-label={t.home}>
        <svg width="30" height="38" viewBox="0 0 30 38" fill="none" aria-hidden="true">
          <path d="M4 5h22L15 20 4 5ZM15 20v12m-7 0h14M8 11h14" stroke="currentColor" strokeWidth="1.6" />
          <circle cx="22" cy="6" r="4" fill="#f7f4ed" stroke="currentColor" strokeWidth="1.6" />
        </svg>
        <span className="multiline">{t.brand}</span>
      </a>
      <button className="new-chat" onClick={reset} disabled={!session || busy}>
        <span aria-hidden="true">+</span> {t.newChat}
      </button>
      <nav aria-label={t.startersLabel} className="starters">
        <h2>{t.startersHeading}</h2>
        {starters.map(([label, text], index) => <button key={label} disabled={busy} onClick={() => choose(text)}>
          <span className="starter-number" aria-hidden="true">{number.format(index + 1).padStart(2, number.format(0))}</span><span>{label}</span>
          <span className="starter-arrow" aria-hidden="true">↗</span>
        </button>)}
      </nav>
      <p className="sidebar-note">{t.sidebarNote}</p>
      <p className="sidebar-detail">{t.sidebarDetail}</p>
    </aside>

    <main>
      <header className="topbar">
        <span className="tagline">{t.tagline}</span>
        <div className="header-controls">
          <label className="language-picker">
            <span>{t.language}</span>
            <select aria-label={t.language} value={language} disabled={busy || connecting}
              onChange={event => setLanguage(event.target.value)}>
              <option value="en" lang="en" dir="ltr">English</option>
              <option value="fa" lang="fa" dir="rtl">فارسی</option>
            </select>
          </label>
        <span className="connection" role="status">{connecting ? t.connecting : !session ? t.disconnected : busy ? t.preparing : t.ready}</span>
        </div>
      </header>
      <section className="conversation" aria-label={t.conversation}>
        {messages.length === 0 && <div className="welcome">
          <div className="glass-study" aria-hidden="true">
            <svg viewBox="0 0 200 140" fill="none">
              <path d="M52 29h96l-48 58-48-58Zm48 58v37m-29 0h58M63 42h74" stroke="currentColor" strokeWidth="1.5" />
              <path d="M66 45h68L100 85 66 45Z" fill="#b96a3d" fillOpacity=".2" />
              <circle cx="137" cy="31" r="20" fill="#f7f4ed" stroke="currentColor" strokeWidth="1.5" />
              <circle cx="137" cy="31" r="14" stroke="currentColor" strokeWidth="1" />
              <path d="m137 17 0 28m-14-14h28m-24-10 20 20m0-20-20 20" stroke="currentColor" />
            </svg>
          </div>
          <h1 className="multiline">{t.welcome}</h1>
          <p className="multiline">{t.intro}</p>
          <div className="quick-starts">
            <button disabled={busy} onClick={() => choose(starters[0][1])}>{t.quickCocktail} <span aria-hidden="true">↗</span></button>
            <button disabled={busy} onClick={() => choose(starters[2][1])}>{t.quickWine} <span aria-hidden="true">↗</span></button>
          </div>
        </div>}
        <div className="messages" role="log" aria-label={t.messages} aria-live="polite">
          {messages.map((message, index) => <article className={`message ${message.role}`} key={index}>
            <h2>{message.role === 'user' ? t.you : t.title}</h2>
            <div className="message-text" dir="auto">{message.text}</div>
          </article>)}
          {busy && <p className="thinking" role="status">{t.thinking}</p>}
          <div ref={end} />
        </div>
      </section>
      <footer className="composer-area">
        {error && <div className="error" role="alert">{t.errors[error] || t.errors.generic}</div>}
        {!session && !connecting && <button className="reconnect" onClick={connect}>{t.reconnect}</button>}
        <form className="composer" onSubmit={send}>
          <label className="sr-only" htmlFor="message">{t.question}</label>
          <textarea id="message" dir="auto" ref={input} value={draft} onChange={event => setDraft(event.target.value)}
            placeholder={t.placeholder} rows="2"
            maxLength={session?.max_input_chars ?? 4000} disabled={!session || busy}
            onKeyDown={event => {
              if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
                event.preventDefault(); event.currentTarget.form.requestSubmit();
              }
            }} />
          <div className="composer-bottom">
            <span>{draft.length ? <bdi dir="ltr">{number.format(draft.length)} / {number.format(session?.max_input_chars ?? 4000)}</bdi> : <><bdi dir="ltr">Enter</bdi> {t.enterHint} · <bdi dir="ltr">Shift + Enter</bdi> {t.shiftHint}</>}</span>
            <button className="send" type="submit" disabled={!session || busy || !draft.trim()}>
              {busy ? t.pleaseWait : t.send} <span aria-hidden="true">↑</span>
            </button>
          </div>
        </form>
        <p className="scope-note">{t.scope}</p>
      </footer>
    </main>
  </div>;
}

