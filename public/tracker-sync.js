/**
 * TrackerSync — Transparent server sync layer for localStorage-based trackers
 *
 * How it works:
 *   - On page load: fetches state from server, merges into localStorage, then lets the tracker render
 *   - On every localStorage write: debounces and pushes the full tracker state to the server
 *   - If server is unreachable: localStorage continues working as normal (offline-first)
 *
 * Usage: Include this script BEFORE the tracker's own <script> block.
 *   <script src="tracker-sync.js" data-tracker-key="my-tracker-key" data-prefix="aws-dea-checklist-"></script>
 *
 * Attributes:
 *   data-tracker-key  — The KV key name used on the server (required)
 *   data-prefix       — localStorage key prefix to sync (for multi-key trackers like the AWS checklist)
 *   data-single-key   — If set, sync only this single localStorage key (for single-blob trackers)
 */

(function () {
  'use strict';

  const SYNC_API = 'https://html-trackers.pages.dev/api';
  const TOKEN_KEY = '_sync_token';
  const SCRIPT_TAG = document.currentScript;
  const TRACKER_KEY = SCRIPT_TAG?.getAttribute('data-tracker-key');
  const PREFIX = SCRIPT_TAG?.getAttribute('data-prefix') || '';
  const SINGLE_KEY = SCRIPT_TAG?.getAttribute('data-single-key') || '';

  if (!TRACKER_KEY) {
    console.warn('[TrackerSync] Missing data-tracker-key attribute');
    return;
  }

  let _debounceTimer = null;
  const DEBOUNCE_MS = 2000;

  function getToken() {
    return localStorage.getItem(TOKEN_KEY) || '';
  }

  // Collect all relevant localStorage entries into one object
  function collectState() {
    if (SINGLE_KEY) {
      const val = localStorage.getItem(SINGLE_KEY);
      return val ? { _single: true, key: SINGLE_KEY, value: val } : null;
    }

    if (PREFIX) {
      const entries = {};
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        if (k.startsWith(PREFIX)) {
          entries[k] = localStorage.getItem(k);
        }
      }
      return { _prefix: true, prefix: PREFIX, entries };
    }

    return null;
  }

  // Apply server state into localStorage
  function applyState(serverData) {
    if (!serverData) return;

    if (serverData._single && serverData.value) {
      localStorage.setItem(serverData.key, serverData.value);
    } else if (serverData._prefix && serverData.entries) {
      Object.entries(serverData.entries).forEach(([k, v]) => {
        localStorage.setItem(k, v);
      });
    }
  }

  // Fetch state from server
  async function loadFromServer() {
    const token = getToken();
    if (!token) return null;

    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 3000);
      const res = await fetch(`${SYNC_API}/api/state/${encodeURIComponent(TRACKER_KEY)}`, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}` },
        signal: controller.signal,
      });
      clearTimeout(timeout);
      if (res.ok) {
        const json = await res.json();
        return json.data;
      }
    } catch (e) {
      // Offline or timeout — that's fine
    }
    return null;
  }

  // Push state to server
  async function saveToServer() {
    const token = getToken();
    if (!token) {
      updateStatus('no-token');
      return;
    }

    const state = collectState();
    if (!state) return;

    try {
      updateStatus('saving');
      const res = await fetch(`${SYNC_API}/api/state/${encodeURIComponent(TRACKER_KEY)}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(state),
      });
      if (res.ok) {
        updateStatus('synced');
      } else {
        updateStatus('error');
      }
    } catch (e) {
      updateStatus('offline');
    }
  }

  // Debounced save
  function scheduleSave() {
    clearTimeout(_debounceTimer);
    _debounceTimer = setTimeout(saveToServer, DEBOUNCE_MS);
  }

  // Intercept localStorage.setItem to trigger sync
  const _origSetItem = Storage.prototype.setItem;
  Storage.prototype.setItem = function (key, value) {
    _origSetItem.call(this, key, value);
    // Only sync if this key belongs to our tracker and this is localStorage (not sessionStorage)
    if (this === localStorage) {
      if ((SINGLE_KEY && key === SINGLE_KEY) || (PREFIX && key.startsWith(PREFIX))) {
        scheduleSave();
      }
    }
  };

  const _origRemoveItem = Storage.prototype.removeItem;
  Storage.prototype.removeItem = function (key) {
    _origRemoveItem.call(this, key);
    if (this === localStorage) {
      if ((SINGLE_KEY && key === SINGLE_KEY) || (PREFIX && key.startsWith(PREFIX))) {
        scheduleSave();
      }
    }
  };

  // Status indicator
  function createStatusIndicator() {
    const el = document.createElement('div');
    el.id = 'sync-status';
    el.style.cssText = 'position:fixed;bottom:12px;right:12px;padding:6px 12px;border-radius:999px;font-size:12px;font-weight:700;background:#f8fafc;border:1px solid #e2e8f0;color:#64748b;z-index:9999;cursor:pointer;user-select:none;box-shadow:0 2px 8px rgba(0,0,0,0.08);';
    el.title = 'Click to set sync token';
    el.textContent = '○ Checking…';
    el.onclick = promptToken;
    document.body.appendChild(el);
    return el;
  }

  let statusEl = null;

  function updateStatus(status) {
    if (!statusEl) return;
    const config = {
      'synced': { text: '● Synced', color: '#16a34a', bg: '#f0fdf4', border: '#bbf7d0' },
      'saving': { text: '↑ Saving…', color: '#2563eb', bg: '#eff6ff', border: '#bfdbfe' },
      'offline': { text: '○ Offline', color: '#d97706', bg: '#fffbeb', border: '#fde68a' },
      'error': { text: '✕ Error', color: '#dc2626', bg: '#fef2f2', border: '#fecaca' },
      'no-token': { text: '○ No token', color: '#6b7280', bg: '#f9fafb', border: '#e5e7eb' },
      'loaded': { text: '● Loaded', color: '#16a34a', bg: '#f0fdf4', border: '#bbf7d0' },
    };
    const c = config[status] || config['offline'];
    statusEl.textContent = c.text;
    statusEl.style.color = c.color;
    statusEl.style.background = c.bg;
    statusEl.style.borderColor = c.border;
  }

  function promptToken() {
    const current = getToken();
    const token = prompt('Enter your sync token:', current);
    if (token !== null) {
      localStorage.setItem(TOKEN_KEY, token);
      updateStatus('saving');
      saveToServer();
    }
  }

  // Init: load from server on page ready, then let tracker render
  async function init() {
    statusEl = createStatusIndicator();

    const token = getToken();
    if (!token) {
      updateStatus('no-token');
      return;
    }

    const serverData = await loadFromServer();
    if (serverData) {
      applyState(serverData);
      updateStatus('loaded');
    } else {
      // No server data — push local to server on first load
      const localState = collectState();
      if (localState && Object.keys(localState.entries || {}).length > 0) {
        await saveToServer();
      } else {
        updateStatus('synced');
      }
    }
  }

  // Run init when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
