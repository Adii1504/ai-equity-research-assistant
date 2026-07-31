const tickerInput = document.getElementById("tickerInput");
const analyseBtn = document.getElementById("analyseBtn");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");

let chartInstances = [];

function formatMarketCap(val) {
  if (val == null) return "N/A";
  if (val >= 1e12) return `$${(val / 1e12).toFixed(2)}T`;
  if (val >= 1e9) return `$${(val / 1e9).toFixed(2)}B`;
  if (val >= 1e6) return `$${(val / 1e6).toFixed(2)}M`;
  return `$${val.toLocaleString()}`;
}

function sentimentBadge(label) {
  const map = { positive: "🟢", negative: "🔴", neutral: "🔵" };
  return map[label] || "🔵";
}

function showStatus(message, type = "info") {
  statusEl.textContent = message;
  statusEl.className = `status ${type}`;
  statusEl.classList.remove("hidden");
}

function hideStatus() {
  statusEl.classList.add("hidden");
}

function destroyCharts() {
  chartInstances.forEach((c) => c.destroy());
  chartInstances = [];
}

function renderChart(canvasId, history) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !history.length) return;

  const ctx = canvas.getContext("2d");
  const chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: history.map((h) => h.date),
      datasets: [{
        label: "Close",
        data: history.map((h) => h.price),
        borderColor: "#3b82f6",
        backgroundColor: "rgba(59, 130, 246, 0.1)",
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          ticks: { color: "#8b9cb3", maxTicksLimit: 6 },
          grid: { color: "rgba(45, 58, 79, 0.5)" },
        },
        y: {
          ticks: { color: "#8b9cb3" },
          grid: { color: "rgba(45, 58, 79, 0.5)" },
        },
      },
    },
  });
  chartInstances.push(chart);
}

function renderReport(report, index) {
  const stock = report.stock;
  const news = report.news;
  const sentiment = report.sentiment;
  const company = stock?.company_name || report.symbol;
  const chartId = `chart-${index}`;

  const cacheBadge = report.cache_info?.from_cache
    ? `⚡ Cached${report.cache_info.stock_ttl_seconds > 0 ? ` (${report.cache_info.stock_ttl_seconds}s left)` : ""}`
    : "🔄 Fresh data";

  const price = stock?.current_price != null ? `$${stock.current_price.toFixed(2)}` : "N/A";
  const delta = stock?.price_change_pct;
  const deltaClass = delta > 0 ? "up" : delta < 0 ? "down" : "";
  const deltaText = delta != null ? `${delta > 0 ? "▲" : "▼"} ${Math.abs(delta).toFixed(2)}%` : "";

  const headlines = (news?.articles || []).slice(0, 8).map((a) => {
    const label = a.sentiment_label || "neutral";
    const score = a.sentiment_score != null ? `${(a.sentiment_score * 100).toFixed(0)}%` : "";
    return `
      <div class="headline">
        ${sentimentBadge(label)} <a href="${a.url}" target="_blank" rel="noopener">${a.title}</a>
        <div class="headline-meta">${a.publisher} · ${a.published_at} · ${label} (${score})</div>
      </div>`;
  }).join("") || `<p class="empty-msg">${news?.error ? `News unavailable: ${news.error}` : "No recent headlines found"}</p>`;

  const llmBlock = report.llm_summary
    ? `
      <details class="llm-section" open>
        <summary>📋 Summary</summary>
        <p>${report.llm_summary}</p>
      </details>
      <details class="llm-section">
        <summary>✅ Key Positives</summary>
        <p>${report.llm_positives || "N/A"}</p>
      </details>
      <details class="llm-section">
        <summary>⚠️ Key Risks</summary>
        <p>${report.llm_risks || "N/A"}</p>
      </details>
      <details class="llm-section">
        <summary>🔮 Outlook</summary>
        <p>${report.llm_outlook || "N/A"}</p>
      </details>`
    : `<p class="empty-msg">Report not available — check GROQ_API_KEY in .env</p>`;

  const errors = report.errors?.length
    ? `<div class="warning-box">Partial data — ${report.errors.length} component(s) unavailable: ${report.errors.join(", ")}</div>`
    : "";

  return `
    <article class="report-card" data-report="${index}">
      <div class="report-header">
        <h2>📈 ${company} (${report.symbol})</h2>
        <span class="cache-badge">${cacheBadge}</span>
      </div>

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
          <div class="metric-value sentiment-${sentiment?.overall_label || "neutral"}">
            ${sentiment ? sentiment.overall_label.charAt(0).toUpperCase() + sentiment.overall_label.slice(1) : "N/A"}
          </div>
          ${sentiment ? `<div class="metric-delta">${(sentiment.overall_score * 100).toFixed(0)}% confidence</div>` : ""}
        </div>
      </div>

      <div class="chart-section">
        <h3>30-Day Price History</h3>
        <div class="chart-wrap">
          <canvas id="${chartId}"></canvas>
        </div>
      </div>

      <div class="columns">
        <div>
          <h3>Recent Headlines</h3>
          ${headlines}
        </div>
        <div>
          <h3>AI Research Note</h3>
          ${llmBlock}
        </div>
      </div>

      <details>
        <summary>⚙️ Performance Metrics</summary>
        <div class="perf-grid">
          <div class="perf-item"><span>Stock Fetch</span>${stock?.fetch_time_ms != null ? `${stock.fetch_time_ms.toFixed(0)}ms` : "N/A"}</div>
          <div class="perf-item"><span>News Fetch</span>${news?.fetch_time_ms != null ? `${news.fetch_time_ms.toFixed(0)}ms` : "N/A"}</div>
          <div class="perf-item"><span>Sentiment</span>${sentiment?.analysis_time_ms != null ? `${sentiment.analysis_time_ms.toFixed(0)}ms` : "N/A"}</div>
          <div class="perf-item"><span>Total Pipeline</span>${report.total_time_ms != null ? `${report.total_time_ms.toFixed(0)}ms` : "N/A"}</div>
        </div>
      </details>

      ${errors}
    </article>`;
}

function renderResults(reports, elapsed) {
  destroyCharts();
  resultsEl.innerHTML = "";

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

    tabs.addEventListener("click", (e) => {
      if (!e.target.classList.contains("tab-btn")) return;
      const idx = e.target.dataset.index;
      tabs.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      e.target.classList.add("active");
      panels.querySelectorAll(".tab-panel").forEach((p) => {
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
}

async function runAnalysis() {
  const raw = tickerInput.value.trim();
  if (!raw) {
    showStatus("Enter a ticker above and click Analyse to generate a research report.", "info");
    return;
  }

  const symbols = raw.split(",").map((s) => s.trim()).filter(Boolean);
  if (!symbols.length) {
    showStatus("Please enter at least one valid ticker symbol.", "error");
    return;
  }

  analyseBtn.disabled = true;
  analyseBtn.innerHTML = '<span class="spinner"></span>Analysing…';
  showStatus(`Researching ${symbols.slice(0, 5).join(", ")}…`, "info");
  resultsEl.innerHTML = "";
  destroyCharts();

  const start = performance.now();

  try {
    const res = await fetch("/api/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbols: symbols.slice(0, 5) }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Request failed (${res.status})`);
    }

    const data = await res.json();
    const elapsed = (performance.now() - start) / 1000;
    renderResults(data.reports, elapsed);
  } catch (err) {
    showStatus(err.message || "Something went wrong. Check the server logs.", "error");
  } finally {
    analyseBtn.disabled = false;
    analyseBtn.textContent = "Analyse →";
  }
}

analyseBtn.addEventListener("click", runAnalysis);
tickerInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") runAnalysis();
});
