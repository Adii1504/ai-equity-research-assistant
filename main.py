"""
main.py
-------
Streamlit frontend for the AI Equity Research Assistant.

Run with:
    streamlit run main.py

This file handles UI only — no business logic here.
All data fetching goes through app.py (the orchestrator).
"""

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

from app import research
from models.stock_model import ResearchReport
from utils.cache import cache

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title = "AI Equity Research Assistant",
    page_icon  = "📊",
    layout     = "wide",
)

# ── Custom CSS — minimal, professional ────────────────────────────────────────
st.markdown("""
<style>
.metric-container { background: #f8f9fa; border-radius: 8px; padding: 12px; }
.sentiment-positive { color: #16a34a; font-weight: 600; }
.sentiment-negative { color: #dc2626; font-weight: 600; }
.sentiment-neutral  { color: #2563eb; font-weight: 600; }
.cache-badge { font-size: 11px; color: #6b7280; background: #f3f4f6;
               padding: 2px 8px; border-radius: 10px; }
.headline-row { padding: 6px 0; border-bottom: 1px solid #f3f4f6; }
</style>
""", unsafe_allow_html=True)


def _sentiment_class(label: str) -> str:
    return f"sentiment-{label.lower()}" if label else "sentiment-neutral"


def _format_price_change(change_pct):
    if change_pct is None:
        return "N/A"
    arrow = "▲" if change_pct > 0 else "▼"
    return f"{arrow} {abs(change_pct):.2f}%"


def _format_market_cap(val):
    if val is None:
        return "N/A"
    if val >= 1e12:
        return f"${val/1e12:.2f}T"
    if val >= 1e9:
        return f"${val/1e9:.2f}B"
    if val >= 1e6:
        return f"${val/1e6:.2f}M"
    return f"${val:,.0f}"


def render_report(report: ResearchReport):
    """Render one research report in the UI."""

    stock     = report.stock
    news      = report.news
    sentiment = report.sentiment

    # ── Header ─────────────────────────────────────────────────────────────
    company_name = (stock.company_name if stock else report.symbol)
    st.subheader(f"📈 {company_name} ({report.symbol})")

    # Cache status badge
    cache_badges = []
    if stock and stock.from_cache:
        remaining = cache.ttl(f"stock:{report.symbol}")
        cache_badges.append(f"Stock: cached ({remaining}s left)")
    if news and news.from_cache:
        cache_badges.append("News: cached")

    if cache_badges:
        st.markdown(
            f'<span class="cache-badge">⚡ {" | ".join(cache_badges)}</span>',
            unsafe_allow_html=True
        )
    else:
        st.markdown('<span class="cache-badge">🔄 Fresh data</span>', unsafe_allow_html=True)

    st.divider()

    # ── Key Metrics (4-column grid) ────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        price = f"${stock.current_price:.2f}" if stock and stock.current_price else "N/A"
        delta = f"{stock.price_change_pct:+.2f}%" if stock and stock.price_change_pct else None
        st.metric("Current Price", price, delta=delta)

    with c2:
        cap = _format_market_cap(stock.market_cap if stock else None)
        st.metric("Market Cap", cap)

    with c3:
        pe = f"{stock.pe_ratio:.1f}x" if stock and stock.pe_ratio else "N/A"
        st.metric("P/E Ratio", pe)

    with c4:
        if sentiment:
            label = sentiment.overall_label.capitalize()
            score = f"{sentiment.overall_score:.0%} confidence"
            st.metric("Sentiment", label, delta=score)
        else:
            st.metric("Sentiment", "N/A")

    # ── 30-Day Price Chart ─────────────────────────────────────────────────
    st.markdown("##### 30-Day Price History")
    try:
        hist = yf.Ticker(report.symbol).history(period="1mo")
        if not hist.empty:
            chart_data = pd.DataFrame({"Price": hist["Close"]})
            st.line_chart(chart_data, use_container_width=True, height=200)
        else:
            st.info("Price history unavailable")
    except Exception:
        st.info("Price chart unavailable")

    # ── Two columns: Headlines + LLM Report ───────────────────────────────
    col_news, col_report = st.columns([1, 1], gap="large")

    with col_news:
        st.markdown("##### Recent Headlines")
        if news and news.articles:
            for article in news.articles[:8]:
                label = article.sentiment_label or "neutral"
                score = article.sentiment_score or 0

                badge_color = {
                    "positive": "🟢",
                    "negative": "🔴",
                    "neutral":  "🔵",
                }.get(label, "🔵")

                with st.container():
                    st.markdown(
                        f"{badge_color} **[{article.title}]({article.url})**  \n"
                        f"<span style='font-size:11px;color:#6b7280;'>"
                        f"{article.publisher} · {article.published_at} · "
                        f"{label.capitalize()} ({score:.0%})"
                        f"</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown("")
        elif news and news.error:
            st.warning(f"News unavailable: {news.error}")
        else:
            st.info("No recent headlines found")

    with col_report:
        st.markdown("##### AI Research Note")
        if report.llm_summary:
            with st.expander("📋 Summary", expanded=True):
                st.write(report.llm_summary)
            with st.expander("✅ Key Positives"):
                st.write(report.llm_positives or "N/A")
            with st.expander("⚠️ Key Risks"):
                st.write(report.llm_risks or "N/A")
            with st.expander("🔮 Outlook"):
                st.write(report.llm_outlook or "N/A")
        else:
            st.info("Report not available — check GROQ_API_KEY in .env")

    # ── Benchmark Metrics (sidebar-style) ─────────────────────────────────
    with st.expander("⚙️ Performance Metrics"):
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Stock Fetch",     f"{stock.fetch_time_ms:.0f}ms"     if stock and stock.fetch_time_ms else "N/A")
        m2.metric("News Fetch",      f"{news.fetch_time_ms:.0f}ms"      if news and news.fetch_time_ms else "N/A")
        m3.metric("Sentiment",       f"{sentiment.analysis_time_ms:.0f}ms" if sentiment and sentiment.analysis_time_ms else "N/A")
        m4.metric("Total Pipeline",  f"{report.total_time_ms:.0f}ms"    if report.total_time_ms else "N/A")

    if report.errors:
        st.warning(f"Partial data — {len(report.errors)} component(s) unavailable: {', '.join(report.errors)}")


# ── Main App ──────────────────────────────────────────────────────────────────
def main():
    st.title("📊 AI Equity Research Assistant")
    st.caption(
        "Automated equity research — fundamentals + news sentiment + LLM analysis. "
        "Enter one or more tickers to generate a research note."
    )

    # ── Input ───────────────────────────────────────────────────────────────
    col_input, col_btn = st.columns([4, 1])

    with col_input:
        ticker_input = st.text_input(
            label       = "Ticker(s)",
            placeholder = "AAPL, MSFT, TCS.NS — separate multiple with commas",
            label_visibility = "collapsed",
        )

    with col_btn:
        run = st.button("Analyse →", use_container_width=True, type="primary")

    # ── Example tickers ─────────────────────────────────────────────────────
    st.markdown(
        "<span style='font-size:12px;color:#6b7280;'>Examples: </span>"
        "<span style='font-size:12px;'>AAPL · TSLA · MSFT · TCS.NS · RELIANCE.NS · INFY.NS</span>",
        unsafe_allow_html=True,
    )

    if not run or not ticker_input.strip():
        st.info("Enter a ticker above and click Analyse to generate a research report.")
        return

    # ── Parse + validate tickers ────────────────────────────────────────────
    symbols = [s.strip().upper() for s in ticker_input.split(",") if s.strip()]
    if not symbols:
        st.error("Please enter at least one valid ticker symbol")
        return

    if len(symbols) > 5:
        st.warning("Maximum 5 tickers per request — using first 5")
        symbols = symbols[:5]

    # ── Run research pipeline ───────────────────────────────────────────────
    with st.spinner(f"Researching {', '.join(symbols)}…"):
        start = datetime.utcnow()
        reports = research(symbols)
        elapsed = (datetime.utcnow() - start).total_seconds()

    # ── Concurrent vs sequential callout ────────────────────────────────────
    if len(symbols) > 1:
        st.success(
            f"✅ Analysed {len(symbols)} tickers concurrently in {elapsed:.1f}s "
            f"(sequential estimate: ~{elapsed * len(symbols):.1f}s)"
        )

    # ── Render each report ───────────────────────────────────────────────────
    if len(reports) > 1:
        tabs = st.tabs([r.symbol for r in reports])
        for tab, report in zip(tabs, reports):
            with tab:
                render_report(report)
    else:
        render_report(reports[0])


if __name__ == "__main__":
    main()
