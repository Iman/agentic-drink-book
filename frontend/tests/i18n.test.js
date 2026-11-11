import assert from 'node:assert/strict';
import { createServer as createHttpServer } from 'node:http';
import { after, afterEach, before, beforeEach, test } from 'node:test';
import { JSDOM } from 'jsdom';
import { createServer } from 'vite';
import { LANGUAGE_KEY, chooseLanguage, translations } from '../src/i18n.js';

let server, App, React, act, createRoot, root, dom, calls;

before(async () => {
  dom = new JSDOM('<!doctype html><html><head></head><body><div id="root"></div></body></html>', {
    url: 'http://localhost:8000',
  });
  Object.assign(globalThis, {
    window: dom.window, document: dom.window.document, localStorage: dom.window.localStorage,
    IS_REACT_ACT_ENVIRONMENT: true, requestAnimationFrame: callback => callback(),
  });
  Object.defineProperty(globalThis, 'navigator', { value: dom.window.navigator, configurable: true });
  dom.window.HTMLElement.prototype.scrollIntoView = () => {};
  ({ default: React, act } = await import('react'));
  ({ createRoot } = await import('react-dom/client'));
  // Attach Vite to an unbound HTTP server so DOM tests never open a network listener.
  server = await createServer({
    server: { middlewareMode: true, ws: { server: createHttpServer() } }, appType: 'custom',
  });
  ({ default: App } = await server.ssrLoadModule('/src/App.jsx'));
});

beforeEach(() => {
  localStorage.clear();
  calls = [];
  globalThis.fetch = async (path, options) => {
    calls.push({ path, ...options });
    const data = path === '/api/chat'
      ? { status: 'answered', reply: 'درود، برای نگرونی ۳۰ ml جین استفاده کنید.' }
      : { csrf: 'synthetic-token', history: [], max_input_chars: 4000 };
    return { ok: true, json: async () => data };
  };
  root = createRoot(document.querySelector('#root'));
});

afterEach(async () => { await act(async () => root.unmount()); });
after(async () => { await server?.close(); dom?.window.close(); });

async function mount() { await act(async () => root.render(React.createElement(App))); }
async function language(value) {
  await act(async () => {
    const select = document.querySelector('select');
    select.value = value;
    select.dispatchEvent(new window.Event('change', { bubbles: true }));
  });
}

test('translation catalogs have the same keys and valid localized starters', () => {
  assert.deepEqual(Object.keys(translations.en).sort(), Object.keys(translations.fa).sort());
  assert.deepEqual(Object.keys(translations.en.errors).sort(), Object.keys(translations.fa.errors).sort());
  assert.equal(translations.en.starters.length, translations.fa.starters.length);
  for (const [label, prompt] of translations.fa.starters) {
    assert.match(label, /[\u0600-\u06ff]/);
    assert.match(prompt, /[\u0600-\u06ff]/);
  }
  assert.equal(chooseLanguage('en', 'fa-IR'), 'en');
  assert.equal(chooseLanguage(null, 'fa-IR'), 'fa');
  assert.equal(chooseLanguage('unsupported', 'de-DE'), 'en');
});

test('switching languages updates direction, labels, title and persisted preference', async () => {
  await mount();
  assert.equal(document.documentElement.dir, 'ltr');
  await language('fa');
  assert.equal(document.documentElement.lang, 'fa');
  assert.equal(document.documentElement.dir, 'rtl');
  assert.equal(document.title, translations.fa.title);
  assert.equal(document.querySelector('textarea').placeholder, translations.fa.placeholder);
  assert.equal(document.querySelector('.send').textContent.trim(), 'ارسال ↑');
  assert.equal(localStorage.getItem(LANGUAGE_KEY), 'fa');
  await language('en');
  assert.equal(document.documentElement.dir, 'ltr');
  assert.equal(document.querySelector('h1').textContent, translations.en.welcome);
});

test('saved Persian preference survives remount and tolerates unavailable storage', async () => {
  localStorage.setItem(LANGUAGE_KEY, 'fa');
  await mount();
  assert.equal(document.documentElement.dir, 'rtl');
  assert.equal(calls[0].headers['X-Chat-Language'], 'fa');
  await act(async () => root.unmount());
  const storage = globalThis.localStorage;
  globalThis.localStorage = { getItem() { throw new Error('blocked'); }, setItem() { throw new Error('blocked'); } };
  try {
    root = createRoot(document.querySelector('#root'));
    await mount();
    await language('fa');
    assert.equal(document.documentElement.dir, 'rtl');
  } finally { globalThis.localStorage = storage; }
});

test('draft is preserved across a language switch and chat sends only the chosen locale', async () => {
  await mount();
  await act(async () => document.querySelector('.quick-starts button').click());
  const draft = document.querySelector('textarea').value;
  await language('fa');
  assert.equal(document.querySelector('textarea').value, draft);
  await act(async () => document.querySelector('form').dispatchEvent(new window.Event('submit', {
    bubbles: true, cancelable: true,
  })));
  const chat = calls.find(call => call.path === '/api/chat');
  assert.equal(chat.headers['X-Chat-Language'], 'fa');
  assert.deepEqual(JSON.parse(chat.body), { message: draft });
  const messages = document.querySelectorAll('.message-text');
  assert.equal(messages.length, 2);
  assert.equal(messages[0].dir, 'auto');
  assert.equal(messages[1].dir, 'auto');
  assert.match(messages[1].textContent, /۳۰ ml/);
});

test('error messages translate when language changes and preserve failed draft', async () => {
  await mount();
  await act(async () => document.querySelector('.quick-starts button').click());
  const draft = document.querySelector('textarea').value;
  globalThis.fetch = async () => ({ ok: false, status: 503, json: async () => ({ code: 'unavailable' }) });
  await act(async () => document.querySelector('form').dispatchEvent(new window.Event('submit', {
    bubbles: true, cancelable: true,
  })));
  assert.equal(document.querySelector('textarea').value, draft);
  assert.equal(document.querySelector('[role="alert"]').textContent, translations.en.errors.unavailable);
  await language('fa');
  assert.equal(document.querySelector('[role="alert"]').textContent, translations.fa.errors.unavailable);
});
