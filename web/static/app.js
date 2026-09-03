/* ==========================================================================
   FinanceCLA — Premium Interactive Frontend
   Greeting · Enhanced Reports · Autocomplete · Theme · Mobile · Toasts
   ========================================================================== */

// ── DOM References ─────────────────────────────────────────────
const tickerInput     = document.getElementById("tickerInput");
const navSearchInput  = document.getElementById("navSearchInput");
const analyseBtn      = document.getElementById("analyseBtn");
const statusEl        = document.getElementById("status");
const resultsEl       = document.getElementById("results");
const heroSection     = document.getElementById("heroSection");
const mainContent     = document.getElementById("mainContent");
const loginModal      = document.getElementById("loginModal");
const openLoginBtn    = document.getElementById("openLoginBtn");
const closeLoginBtn   = document.getElementById("closeLoginBtn");
const heroSearch      = document.getElementById("heroSearch");
const tickerTrack     = document.getElementById("tickerTrack");
const heroGreeting    = document.getElementById("heroGreeting");
const themeToggleBtn  = document.getElementById("themeToggleBtn");
const hamburgerBtn    = document.getElementById("hamburgerBtn");
const navLinks        = document.getElementById("navLinks");
const navSearchDrop   = document.getElementById("navSearchDropdown");
const toastContainer  = document.getElementById("toastContainer");
const currentPage     = document.body.dataset.page || "home";

let chartInstances = [];
let stockCatalog   = [];  // filled by fetchCatalog()

// ── Theme Toggle ───────────────────────────────────────────────
function initTheme() {
  const saved = localStorage.getItem("financecla_theme");
  if (saved === "light") {
    document.documentElement.setAttribute("data-theme", "light");
    if (themeToggleBtn) themeToggleBtn.textContent = "☀️";
  }
}
initTheme();

themeToggleBtn?.addEventListener("click", () => {
  const isLight = document.documentElement.getAttribute("data-theme") === "light";
  if (isLight) {
    document.documentElement.removeAttribute("data-theme");
    localStorage.setItem("financecla_theme", "dark");
    themeToggleBtn.textContent = "🌙";
  } else {
    document.documentElement.setAttribute("data-theme", "light");
    localStorage.setItem("financecla_theme", "light");
    themeToggleBtn.textContent = "☀️";
  }
});

// ── Mobile Hamburger ───────────────────────────────────────────
hamburgerBtn?.addEventListener("click", () => {
  hamburgerBtn.classList.toggle("active");
  navLinks?.classList.toggle("mobile-open");
});

// Close mobile menu when clicking a link
navLinks?.querySelectorAll(".nav-link").forEach(link => {
  link.addEventListener("click", () => {
    hamburgerBtn?.classList.remove("active");
    navLinks.classList.remove("mobile-open");
  });
});

// ── Time-of-Day Greeting ───────────────────────────────────────
function setGreeting() {
  if (!heroGreeting) return;
  const hour = new Date().getHours();
  let greeting;
  if (hour < 5)       greeting = "Burning the midnight oil? Let's research.";
  else if (hour < 12) greeting = "Good morning — ready to research?";
  else if (hour < 17) greeting = "Good afternoon — what should we analyse?";
  else if (hour < 21) greeting = "Good evening — ready to research?";
  else                greeting = "Late night research mode — let's dive in.";

  const savedEmail = localStorage.getItem("financecla_user_email");
  if (savedEmail) {
    const name = savedEmail.split("@")[0];
    greeting = greeting.replace("ready to research?", `${name}!`).replace("Let's research.", `${name}.`).replace("what should we analyse?", `${name}!`).replace("let's dive in.", `${name}.`);
  }
  heroGreeting.textContent = greeting;
}
setGreeting();

// ── Ticker Strip Duplication ───────────────────────────────────
if (tickerTrack) {
  tickerTrack.innerHTML += tickerTrack.innerHTML;
}

// ── Auth Helpers ───────────────────────────────────────────────
function authHeaders(extra = {}) {
  const headers = { ...extra };
  const token = localStorage.getItem("financecla_token");
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

function authFetch(url, options = {}) {
  const headers = authHeaders(options.headers || {});
  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  return fetch(url, { ...options, headers });
}

// ── Toast System ───────────────────────────────────────────────
function showToast(message, type = "info") {
  if (!toastContainer) return;
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  const icons = { success: "✅", error: "❌", info: "ℹ️" };
  toast.innerHTML = `<span>${icons[type] || "ℹ️"}</span> ${message}`;
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.classList.add("removing");
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

// ── URL Prefill ────────────────────────────────────────────────
const urlParams = new URLSearchParams(window.location.search);
const prefillTicker = urlParams.get("ticker");
if (prefillTicker && tickerInput) {
  tickerInput.value = prefillTicker;
  if (navSearchInput) navSearchInput.value = prefillTicker;
  window.addEventListener("DOMContentLoaded", () => runAnalysis());
}

// ── Input Sync ─────────────────────────────────────────────────
function syncSearchInputs(from, to) {
  from?.addEventListener("input", () => { if (to) to.value = from.value; });
}
if (navSearchInput && tickerInput) {
  syncSearchInputs(tickerInput, navSearchInput);
  syncSearchInputs(navSearchInput, tickerInput);
}

function setTicker(symbol) {
  if (!tickerInput) {
    window.location.href = `/?ticker=${encodeURIComponent(symbol)}`;
    return;
  }
  tickerInput.value = symbol;
  if (navSearchInput) navSearchInput.value = symbol;
  tickerInput.focus();
  heroSearch?.scrollIntoView({ behavior: "smooth", block: "center" });
}

// ── Search Autocomplete ────────────────────────────────────────
async function fetchCatalog() {
  try {
    const res = await fetch("/api/stocks");
    if (res.ok) {
      const data = await res.json();
      stockCatalog = data.stocks || [];
    }
  } catch {}
}
fetchCatalog();

function renderSearchDropdown(input, dropdown, query) {
  if (!dropdown || !query || query.length < 1) {
    dropdown?.classList.remove("active");
    return;
  }
  const q = query.toUpperCase();
  const matches = stockCatalog.filter(s =>
    s.symbol.toUpperCase().includes(q) ||
    s.name.toUpperCase().includes(q)
  ).slice(0, 8);

  if (!matches.length) {
    dropdown.classList.remove("active");
    return;
  }

  dropdown.innerHTML = `<div class="dropdown-header">Stocks</div>` +
    matches.map(s => `
      <div class="dropdown-item" data-symbol="${s.symbol}">
        <div class="item-left">
          <span class="item-symbol">${s.symbol}</span>
          <span class="item-name">${s.name}</span>
        </div>
        <span class="item-sector">${s.sector}</span>
      </div>
    `).join("");

  dropdown.classList.add("active");

  dropdown.querySelectorAll(".dropdown-item").forEach(item => {
    item.addEventListener("click", () => {
      const sym = item.dataset.symbol;
      setTicker(sym);
      dropdown.classList.remove("active");
    });
  });
}

navSearchInput?.addEventListener("input", (e) => {
  renderSearchDropdown(navSearchInput, navSearchDrop, e.target.value.trim());
});

navSearchInput?.addEventListener("blur", () => {
  setTimeout(() => navSearchDrop?.classList.remove("active"), 200);
});

// ── Formatters ─────────────────────────────────────────────────
function formatMarketCap(val) {
  if (val == null) return "N/A";
  if (val >= 1e12) return `$${(val / 1e12).toFixed(2)}T`;
  if (val >= 1e9)  return `$${(val / 1e9).toFixed(2)}B`;
  if (val >= 1e6)  return `$${(val / 1e6).toFixed(2)}M`;
  return `$${val.toLocaleString()}`;
}

function formatPrice(val) {
  if (val == null) return "N/A";
  return `$${val.toFixed(2)}`;
}

// ── Status Display ─────────────────────────────────────────────
function showStatus(message, type = "info") {
  if (!statusEl) return;
  statusEl.textContent = message;
  statusEl.className = `status ${type}`;
  statusEl.classList.remove("hidden");
}

function hideStatus() {
  statusEl?.classList.add("hidden");
}

// ── Chart Management ───────────────────────────────────────────
function destroyCharts() {
  chartInstances.forEach(c => c.destroy());
  chartInstances = [];
}

function renderChart(canvasId, history) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !history.length) return;

  const isLight = document.documentElement.getAttribute("data-theme") === "light";
  const gridColor = isLight ? "rgba(0,0,0,0.06)" : "rgba(255,255,255,0.06)";
  const tickColor = isLight ? "#8896a8" : "#5a6578";

  const prices = history.map(h => h.price);
  const isUp = prices[prices.length - 1] >= prices[0];
  const lineColor = isUp ? "#34d399" : "#fb7185";
  const fillColor = isUp ? "rgba(52, 211, 153, 0.08)" : "rgba(251, 113, 133, 0.08)";

  const ctx = canvas.getContext("2d");
  const chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: history.map(h => h.date),
      datasets: [{
        label: "Close",
        data: prices,
        borderColor: lineColor,
        backgroundColor: fillColor,
        fill: true,
        tension: 0.35,
        pointRadius: 0,
        pointHoverRadius: 4,
        pointHoverBackgroundColor: lineColor,
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { intersect: false, mode: "index" },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: isLight ? "#ffffff" : "#1a2234",
          titleColor: isLight ? "#0c1222" : "#f0f2f5",
          bodyColor: isLight ? "#4a5568" : "#94a3b8",
          borderColor: isLight ? "#e2e7f0" : "rgba(255,255,255,0.08)",
          borderWidth: 1,
          padding: 10,
          cornerRadius: 8,
          displayColors: false,
          callbacks: {
            label: ctx => `$${ctx.parsed.y.toFixed(2)}`,
          },
        },
      },
      scales: {
        x: { ticks: { color: tickColor, maxTicksLimit: 6, font: { size: 11 } }, grid: { color: gridColor } },
        y: { ticks: { color: tickColor, font: { size: 11 } }, grid: { color: gridColor } },
      },
    },
  });
  chartInstances.push(chart);
}

// ── Verdict Derivation ─────────────────────────────────────────
function deriveVerdict(report) {
  const sentiment = report.sentiment;
  const stock = report.stock;
  const delta = stock?.price_change_pct;

  let score = 0;
  if (sentiment) {
    if (sentiment.overall_label === "positive") score += 2;
    else if (sentiment.overall_label === "negative") score -= 2;
  }
  if (delta != null) {
    if (delta > 1) score += 1;
    else if (delta < -1) score -= 1;
  }

  if (score >= 2) return { label: "Bullish", class: "bullish", emoji: "📈" };
  if (score <= -2) return { label: "Bearish", class: "bearish", emoji: "📉" };
  return { label: "Neutral", class: "neutral", emoji: "➡️" };
}

// ── Skeleton Loader ────────────────────────────────────────────
function showSkeleton() {
  if (!resultsEl) return;
  resultsEl.innerHTML = `
    <div class="skeleton-card">
      <div class="skeleton-header">
        <div class="skeleton skeleton-avatar"></div>
        <div style="flex:1">
          <div class="skeleton skeleton-line medium"></div>
          <div class="skeleton skeleton-line short"></div>
        </div>
      </div>
      <div class="skeleton-metrics">
        <div class="skeleton skeleton-metric"></div>
        <div class="skeleton skeleton-metric"></div>
        <div class="skeleton skeleton-metric"></div>
        <div class="skeleton skeleton-metric"></div>
      </div>
      <div class="skeleton skeleton-chart"></div>
    </div>`;
}

// ── Report Renderer ────────────────────────────────────────────
function renderReport(report, index) {
  const stock     = report.stock;
  const news      = report.news;
  const sentiment = report.sentiment;
  const company   = stock?.company_name || report.symbol;
  const chartId   = `chart-${index}`;
  const initials  = company.substring(0, 2).toUpperCase();
  const verdict   = deriveVerdict(report);

  const cacheBadge = report.cache_info?.from_cache
    ? `⚡ Cached${report.cache_info.stock_ttl_seconds > 0 ? ` (${report.cache_info.stock_ttl_seconds}s)` : ""}`
    : "🔄 Fresh";

  const price     = formatPrice(stock?.current_price);
  const delta     = stock?.price_change_pct;
  const deltaClass = delta > 0 ? "up" : delta < 0 ? "down" : "";
  const deltaText  = delta != null ? `${delta > 0 ? "▲" : "▼"} ${Math.abs(delta).toFixed(2)}%` : "";

  // Sentiment meter
  const sentScore     = sentiment?.overall_score ?? 0;
  const sentLabel     = sentiment?.overall_label || "neutral";
  const sentPercent   = (sentScore * 100).toFixed(0);
  const sentMeter     = sentiment ? `
    <div class="sentiment-meter">
      <div class="sentiment-fill ${sentLabel}" style="width: ${sentPercent}%"></div>
    </div>` : "";

  // Headlines
  const headlines = (news?.articles || []).slice(0, 6).map(a => {
    const label = a.sentiment_label || "neutral";
    const score = a.sentiment_score != null ? `${(a.sentiment_score * 100).toFixed(0)}%` : "";
    return `
      <a href="${a.url}" target="_blank" rel="noopener" class="headline-item">
        <span class="headline-title">${a.title}</span>
        <span class="headline-meta">
          <span class="headline-badge ${label}">${label}</span>
          ${score ? `<span>${score}</span>` : ""}
          <span>${a.publisher}</span>
          <span>${a.published_at}</span>
        </span>
      </a>`;
  }).join("") || `<p class="empty-msg">${news?.error ? `News unavailable: ${news.error}` : "No recent headlines found"}</p>`;

  // AI Insight blocks
  const llmBlock = report.llm_summary
    ? `
      <div class="insight-block">
        <h4>📋 Summary</h4>
        <p>${report.llm_summary}</p>
      </div>
      ${report.llm_positives ? `
      <div class="insight-block positive">
        <h4>✅ Key Positives</h4>
        <p>${report.llm_positives}</p>
      </div>` : ""}
      ${report.llm_risks ? `
      <div class="insight-block risk">
        <h4>⚠️ Key Risks</h4>
        <p>${report.llm_risks}</p>
      </div>` : ""}
      ${report.llm_outlook ? `
      <div class="insight-block outlook">
        <h4>🔮 Outlook</h4>
        <p>${report.llm_outlook}</p>
      </div>` : ""}`
    : `<p class="empty-msg">AI report unavailable — check GROQ_API_KEY in .env</p>`;

  // Performance pills
  const perfPills = [
    stock?.fetch_time_ms != null ? `Stock ${stock.fetch_time_ms.toFixed(0)}ms` : null,
    news?.fetch_time_ms != null  ? `News ${news.fetch_time_ms.toFixed(0)}ms` : null,
    sentiment?.analysis_time_ms != null ? `Sentiment ${sentiment.analysis_time_ms.toFixed(0)}ms` : null,
    report.total_time_ms != null ? `Total ${report.total_time_ms.toFixed(0)}ms` : null,
  ].filter(Boolean).map(t => `<span class="perf-pill">${t}</span>`).join("");

  // Errors
  const errors = report.errors?.length
    ? `<div class="warning-box">⚠ Partial data — ${report.errors.length} component(s) unavailable: ${report.errors.join(", ")}</div>`
    : "";

  // Verdict banner
  const verdictSummary = report.llm_summary
    ? report.llm_summary.split(". ").slice(0, 2).join(". ") + "."
    : `${company} is currently showing ${sentLabel} sentiment signals.`;

  return `
    <article class="report-card" data-report="${index}">
      <!-- Header -->
      <div class="report-header">
        <div class="report-title-area">
          <div class="report-company-logo">${initials}</div>
          <div class="report-title-text">
            <h2>${company}</h2>
            <span class="report-symbol-pill">${report.symbol}</span>
          </div>
        </div>
        <div class="report-header-right">
          <span class="cache-badge">${cacheBadge}</span>
        </div>
      </div>

      <!-- Verdict Banner -->
      <div class="verdict-banner ${verdict.class}">
        <span class="verdict-badge ${verdict.class}">${verdict.emoji} ${verdict.label}</span>
        <span class="verdict-text">${verdictSummary}</span>
      </div>

      <!-- Metrics -->
      <div class="metrics">
        <div class="metric">
          <div class="metric-label">Current Price</div>
          <div class="metric-value">${price}</div>
          ${deltaText ? `<div class="metric-delta ${deltaClass}">${deltaText}</div>` : ""}
        </div>
        <div class="metric">
          <div class="metric-label">Market Cap</div>
          <div class="metric-value">${formatMarketCap(stock?.market_cap)}</div>
        </div>
        <div class="metric">
          <div class="metric-label">P/E Ratio</div>
          <div class="metric-value">${stock?.pe_ratio != null ? `${stock.pe_ratio.toFixed(1)}x` : "N/A"}</div>
        </div>
        <div class="metric">
          <div class="metric-label">Sentiment</div>
          <div class="metric-value">${sentiment ? sentLabel.charAt(0).toUpperCase() + sentLabel.slice(1) : "N/A"}</div>
          ${sentiment ? `<div class="metric-delta">${sentPercent}% confidence</div>` : ""}
          ${sentMeter}
        </div>
      </div>

      <!-- Chart -->
      <div class="chart-section">
        <div class="chart-header">
          <h3>📈 30-Day Price History</h3>
        </div>
        <div class="chart-wrap">
          <canvas id="${chartId}"></canvas>
        </div>
      </div>

      <!-- Two-Column: Headlines + AI Analysis -->
      <div class="columns">
        <div class="column-card">
          <h3>📰 Recent Headlines</h3>
          <div class="headline-list">${headlines}</div>
        </div>
        <div class="column-card">
          <h3>🧠 AI Research Note</h3>
          ${llmBlock}
        </div>
      </div>

      <!-- Performance Footer -->
      <div class="report-footer-meta">
        <div class="perf-pills">${perfPills}</div>
        <span>Generated ${new Date(report.generated_at).toLocaleString()}</span>
      </div>

      ${errors}
    </article>`;
}

// ── Render Results ─────────────────────────────────────────────
function renderResults(reports, elapsed) {
  destroyCharts();
  resultsEl.innerHTML = "";
  heroSection?.classList.add("hidden");
  mainContent?.classList.add("has-results");

  if (reports.length > 1) {
    showStatus(`✅ Analysed ${reports.length} tickers in ${elapsed.toFixed(1)}s (concurrent)`, "success");
  } else {
    hideStatus();
  }

  if (reports.length > 1) {
    const tabs = document.createElement("div");
    tabs.className = "tabs";
    const panels = document.createElement("div");

    reports.forEach((report, i) => {
      const btn = document.createElement("button");
      btn.className = `tab-btn${i === 0 ? " active" : ""}`;
      btn.textContent = report.symbol;
      btn.dataset.index = i;
      tabs.appendChild(btn);

      const panel = document.createElement("div");
      panel.className = "tab-panel";
      panel.dataset.index = i;
      panel.style.display = i === 0 ? "block" : "none";
      panel.innerHTML = renderReport(report, i);
      panels.appendChild(panel);
    });

    tabs.addEventListener("click", e => {
      if (!e.target.classList.contains("tab-btn")) return;
      const idx = e.target.dataset.index;
      tabs.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      e.target.classList.add("active");
      panels.querySelectorAll(".tab-panel").forEach(p => {
        p.style.display = p.dataset.index === idx ? "block" : "none";
      });
    });

    resultsEl.appendChild(tabs);
    resultsEl.appendChild(panels);
  } else {
    resultsEl.innerHTML = renderReport(reports[0], 0);
  }

  reports.forEach((report, i) => {
    if (report.price_history?.length) {
      renderChart(`chart-${i}`, report.price_history);
    }
  });

  mainContent?.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ── Run Analysis ───────────────────────────────────────────────
async function runAnalysis() {
  if (!tickerInput || !analyseBtn) return;
  const raw = tickerInput.value.trim();
  if (!raw) {
    showToast("Enter a ticker above and click Analyse.", "info");
    heroSearch?.scrollIntoView({ behavior: "smooth", block: "center" });
    return;
  }

  const symbols = raw.split(",").map(s => s.trim()).filter(Boolean);
  if (!symbols.length) {
    showToast("Please enter at least one valid ticker symbol.", "error");
    return;
  }

  analyseBtn.disabled = true;
  analyseBtn.innerHTML = '<span class="spinner"></span>Analysing…';
  showStatus(`Researching ${symbols.slice(0, 5).join(", ")}…`, "info");
  showSkeleton();
  destroyCharts();

  const start = performance.now();

  try {
    const res = await authFetch("/api/research", {
      method: "POST",
      body: JSON.stringify({ symbols: symbols.slice(0, 5) }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Request failed (${res.status})`);
    }

    const data = await res.json();
    const elapsed = (performance.now() - start) / 1000;
    renderResults(data.reports, elapsed);
    showToast(`Analysis complete for ${data.reports.map(r => r.symbol).join(", ")}`, "success");
  } catch (err) {
    showStatus(err.message || "Something went wrong. Check the server logs.", "error");
    showToast(err.message || "Analysis failed", "error");
    resultsEl.innerHTML = "";
  } finally {
    analyseBtn.disabled = false;
    analyseBtn.textContent = "Analyse →";
  }
}

// ── Event Listeners (Home Page) ────────────────────────────────
analyseBtn?.addEventListener("click", runAnalysis);
tickerInput?.addEventListener("keydown", e => { if (e.key === "Enter") runAnalysis(); });
navSearchInput?.addEventListener("keydown", e => { if (e.key === "Enter") runAnalysis(); });

// Chip & mega-link clicks
document.querySelectorAll(".chip[data-ticker], .mega-link[data-ticker]").forEach(el => {
  el.addEventListener("click", e => {
    e.preventDefault();
    const symbol = el.dataset.ticker;
    if (symbol) setTicker(symbol);
    document.querySelectorAll(".nav-item.open").forEach(item => item.classList.remove("open"));
  });
});

// Mega menu dropdowns
document.querySelectorAll(".nav-item.has-dropdown").forEach(item => {
  const btn = item.querySelector("[data-dropdown]");
  btn?.addEventListener("click", e => {
    e.stopPropagation();
    const isOpen = item.classList.contains("open");
    document.querySelectorAll(".nav-item.open").forEach(i => i.classList.remove("open"));
    if (!isOpen) item.classList.add("open");
  });
});

document.addEventListener("click", () => {
  document.querySelectorAll(".nav-item.open").forEach(i => i.classList.remove("open"));
});

// Ctrl+K focus search
document.addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key === "k") {
    e.preventDefault();
    navSearchInput?.focus();
  }
  if (e.key === "Escape") closeLogin();
});

// ── Login Modal ────────────────────────────────────────────────
function openLogin() {
  loginModal?.classList.remove("hidden");
  document.body.style.overflow = "hidden";
}

function closeLogin() {
  loginModal?.classList.add("hidden");
  document.body.style.overflow = "";
}

function setLoggedInUI(email) {
  if (!openLoginBtn) return;
  openLoginBtn.textContent = email.split("@")[0];
  openLoginBtn.onclick = () => { window.location.href = "/profile"; };
  setGreeting(); // re-greet with name
}

function logout() {
  localStorage.removeItem("financecla_token");
  localStorage.removeItem("financecla_user_email");
  window.location.href = "/";
}

openLoginBtn?.addEventListener("click", () => {
  if (localStorage.getItem("financecla_token")) {
    window.location.href = "/profile";
  } else {
    openLogin();
  }
});

closeLoginBtn?.addEventListener("click", closeLogin);
loginModal?.addEventListener("click", e => { if (e.target === loginModal) closeLogin(); });

// Restore session
const savedUser = localStorage.getItem("financecla_user_email");
if (savedUser) setLoggedInUI(savedUser);

// ── Auth Form ──────────────────────────────────────────────────
const authForm      = document.getElementById("authForm");
const authEmail     = document.getElementById("authEmail");
const authPassword  = document.getElementById("authPassword");
const authError     = document.getElementById("authError");
const authSubmitBtn = document.getElementById("authSubmitBtn");
const loginTabBtn   = document.getElementById("loginTabBtn");
const signupTabBtn  = document.getElementById("signupTabBtn");

let authMode = "login";

function setAuthMode(mode) {
  authMode = mode;
  loginTabBtn?.classList.toggle("active", mode === "login");
  signupTabBtn?.classList.toggle("active", mode === "signup");
  if (authSubmitBtn) authSubmitBtn.textContent = mode === "login" ? "Log In" : "Sign Up";
  authError?.classList.add("hidden");
}

loginTabBtn?.addEventListener("click", () => setAuthMode("login"));
signupTabBtn?.addEventListener("click", () => setAuthMode("signup"));

authForm?.addEventListener("submit", async e => {
  e.preventDefault();
  authError?.classList.add("hidden");
  if (authSubmitBtn) { authSubmitBtn.disabled = true; authSubmitBtn.textContent = "Please wait…"; }

  const endpoint = authMode === "login" ? "/api/auth/login" : "/api/auth/signup";

  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: authEmail.value, password: authPassword.value }),
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) throw new Error(data.detail || "Something went wrong. Please try again.");

    localStorage.setItem("financecla_token", data.token);
    localStorage.setItem("financecla_user_email", data.user.email);
    setLoggedInUI(data.user.email);
    closeLogin();
    showToast(`Welcome${authMode === "signup" ? " aboard" : " back"}, ${data.user.email.split("@")[0]}! 🎉`, "success");
  } catch (err) {
    if (authError) { authError.textContent = err.message; authError.classList.remove("hidden"); }
  } finally {
    if (authSubmitBtn) {
      authSubmitBtn.disabled = false;
      authSubmitBtn.textContent = authMode === "login" ? "Log In" : "Sign Up";
    }
  }
});

// ── Secondary Page Loaders ─────────────────────────────────────

async function loadStocksPage() {
  const status   = document.getElementById("pageStatus");
  const filterBar = document.getElementById("stocksFilterBar");
  const tableWrap = document.getElementById("stocksTableWrap");
  const body     = document.getElementById("stocksBody");
  const filterInput = document.getElementById("stockFilterInput");
  const sectorPills = document.getElementById("sectorPills");

  try {
    const res = await fetch("/api/stocks");
    if (!res.ok) throw new Error("Failed to load stocks");
    const data = await res.json();
    const stocks = data.stocks;

    // Build sector pills
    const sectors = [...new Set(stocks.map(s => s.sector))].sort();
    if (sectorPills) {
      sectorPills.innerHTML = `<button class="sector-btn active" data-sector="all">All</button>` +
        sectors.map(s => `<button class="sector-btn" data-sector="${s}">${s}</button>`).join("");

      let activeSector = "all";
      sectorPills.addEventListener("click", e => {
        if (!e.target.classList.contains("sector-btn")) return;
        activeSector = e.target.dataset.sector;
        sectorPills.querySelectorAll(".sector-btn").forEach(b => b.classList.remove("active"));
        e.target.classList.add("active");
        filterStocks();
      });

      function filterStocks() {
        const q = filterInput?.value?.toUpperCase() || "";
        body.innerHTML = stocks
          .filter(s => activeSector === "all" || s.sector === activeSector)
          .filter(s => s.symbol.toUpperCase().includes(q) || s.name.toUpperCase().includes(q))
          .map(s => `
            <tr>
              <td class="symbol-cell">${s.symbol}</td>
              <td>${s.name}</td>
              <td>${s.sector}</td>
              <td><a class="btn-link-action" href="/?ticker=${encodeURIComponent(s.symbol)}">Analyse →</a></td>
            </tr>`).join("");
      }

      filterInput?.addEventListener("input", filterStocks);
      filterStocks();
    } else {
      body.innerHTML = stocks.map(s => `
        <tr>
          <td class="symbol-cell">${s.symbol}</td>
          <td>${s.name}</td>
          <td>${s.sector}</td>
          <td><a class="btn-link-action" href="/?ticker=${encodeURIComponent(s.symbol)}">Analyse →</a></td>
        </tr>`).join("");
    }

    status?.classList.add("hidden");
    filterBar?.classList.remove("hidden");
    tableWrap?.classList.remove("hidden");
  } catch (err) {
    if (status) { status.textContent = err.message; status.className = "status error"; }
  }
}

async function loadFundsPage() {
  const status = document.getElementById("pageStatus");
  const grid   = document.getElementById("fundsGrid");
  try {
    const res = await fetch("/api/funds");
    if (!res.ok) throw new Error("Failed to load funds");
    const data = await res.json();
    grid.innerHTML = data.funds.map(f => {
      const riskClass = f.risk.toLowerCase().includes("high") ? "risk-high"
        : f.risk.toLowerCase().includes("moderate") ? "risk-moderate" : "risk-low";
      return `
      <article class="fund-card">
        <h3>${f.name}</h3>
        <div class="fund-meta">${f.category} · <span class="${riskClass}">${f.risk} risk</span></div>
        <div class="fund-stats">
          <div><span>NAV</span>₹${f.nav.toFixed(2)}</div>
          <div><span>1Y Return</span>${f.returns_1y_pct}%</div>
          <div><span>3Y Return</span>${f.returns_3y_pct}%</div>
          <div><span>Expense</span>${f.expense_ratio_pct}%</div>
        </div>
      </article>`;
    }).join("");
    status?.classList.add("hidden");
    grid?.classList.remove("hidden");
  } catch (err) {
    if (status) { status.textContent = err.message; status.className = "status error"; }
  }
}

async function loadRecommendPage() {
  const status = document.getElementById("pageStatus");
  const list   = document.getElementById("recommendList");
  const badge  = document.getElementById("personalisedBadge");
  try {
    const res = await authFetch("/api/recommend?limit=5");
    if (!res.ok) throw new Error("Failed to load recommendations");
    const data = await res.json();
    if (data.personalised) badge?.classList.remove("hidden");

    list.innerHTML = data.recommendations.map(r => {
      const maxScore = 30;
      const pct = Math.min(100, Math.max(5, ((r.score + 10) / maxScore) * 100));
      return `
      <article class="recommend-card">
        <h3>${r.name} <span class="report-symbol-pill">${r.symbol}</span></h3>
        <div class="recommend-meta">${r.sector}</div>
        <div class="recommend-stats">
          <div><span>Price</span>${r.current_price != null ? `$${r.current_price.toFixed(2)}` : "N/A"}</div>
          <div><span>Change</span>${r.price_change_pct != null ? `${r.price_change_pct.toFixed(2)}%` : "N/A"}</div>
          <div><span>P/E</span>${r.pe_ratio != null ? `${r.pe_ratio.toFixed(1)}x` : "N/A"}</div>
        </div>
        <div class="score-bar-wrap">
          <div class="score-bar"><div class="score-bar-fill" style="width: ${pct}%"></div></div>
          <div class="score-label">Score: ${r.score}</div>
        </div>
        <ul class="recommend-reasons">${r.reasons.map(reason => `<li>${reason}</li>`).join("")}</ul>
        <a class="btn-link-action" href="/?ticker=${encodeURIComponent(r.symbol)}">Analyse this stock →</a>
      </article>`;
    }).join("");
    status?.classList.add("hidden");
    list?.classList.remove("hidden");
  } catch (err) {
    if (status) { status.textContent = err.message; status.className = "status error"; }
  }
}

async function loadProfilePage() {
  const status       = document.getElementById("pageStatus");
  const card         = document.getElementById("profileCard");
  const historyCard  = document.getElementById("historyCard");
  const token        = localStorage.getItem("financecla_token");

  if (!token) {
    if (status) { status.textContent = "Please log in to view your profile."; status.className = "loading-msg"; }
    setTimeout(openLogin, 300);
    return;
  }

  try {
    const res = await authFetch("/api/auth/me");
    if (!res.ok) throw new Error("Session expired — please log in again");
    const user = await res.json();
    const profileEmail   = document.getElementById("profileEmail");
    const profileCreated = document.getElementById("profileCreated");
    const profileAvatar  = document.getElementById("profileAvatar");

    if (profileEmail)   profileEmail.textContent = user.email;
    if (profileCreated) profileCreated.textContent = user.created_at ? new Date(user.created_at).toLocaleDateString() : "—";
    if (profileAvatar)  profileAvatar.textContent = user.email.charAt(0).toUpperCase();

    status?.classList.add("hidden");
    card?.classList.remove("hidden");

    // Load search history
    try {
      const hRes = await authFetch("/api/auth/history");
      if (hRes.ok) {
        const hData = await hRes.json();
        const timeline = document.getElementById("historyTimeline");
        if (timeline && hData.history.length) {
          timeline.innerHTML = hData.history.map(h => `
            <a href="/?ticker=${encodeURIComponent(h.symbol)}" class="history-item">
              <span class="history-symbol">${h.symbol}</span>
              <span class="history-sector">${h.sector || "—"}</span>
              <span class="history-time">${h.searched_at ? new Date(h.searched_at).toLocaleDateString() : ""}</span>
            </a>`).join("");
        } else if (timeline) {
          timeline.innerHTML = `<p class="history-empty">No research history yet. Analyse a stock to get started!</p>`;
        }
        historyCard?.classList.remove("hidden");
      }
    } catch {}
  } catch (err) {
    if (status) { status.textContent = err.message; status.className = "status error"; }
  }
}

document.getElementById("logoutBtn")?.addEventListener("click", logout);

// ── Page Router ────────────────────────────────────────────────
if (currentPage === "stocks")    loadStocksPage();
if (currentPage === "funds")     loadFundsPage();
if (currentPage === "recommend") loadRecommendPage();
if (currentPage === "profile")   loadProfilePage();