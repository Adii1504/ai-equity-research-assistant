"""
models/stock_model.py
---------------------
Data contracts (dataclasses) for the entire project.
Every module reads/writes these — never raw dicts.

ADR: Why dataclasses over dicts?
  - Type safety catches bugs at definition time
  - IDE autocomplete works correctly
  - Interviewers see you understand data contracts
  - Easy to serialize to JSON for caching
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
from typing import Optional, List


@dataclass
class StockData:
    symbol:          str
    company_name:    str
    current_price:   Optional[float]    = None
    previous_close:  Optional[float]    = None
    price_change:    Optional[float]    = None          # absolute
    price_change_pct:Optional[float]    = None          # percentage
    market_cap:      Optional[float]    = None
    pe_ratio:        Optional[float]    = None
    volume:          Optional[int]      = None
    week_52_high:    Optional[float]    = None
    week_52_low:     Optional[float]    = None
    sector:          Optional[str]      = None
    industry:        Optional[str]      = None
    fetch_time_ms:   Optional[float]    = None          # latency metric
    from_cache:      bool               = False

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "StockData":
        return cls(**json.loads(data))


@dataclass
class NewsArticle:
    title:          str
    publisher:      str
    published_at:   str
    url:            str
    description:    Optional[str] = None
    sentiment_label:Optional[str] = None               # positive/neutral/negative
    sentiment_score:Optional[float] = None             # confidence 0–1


@dataclass
class NewsData:
    symbol:         str
    articles:       List[NewsArticle] = field(default_factory=list)
    fetch_time_ms:  Optional[float]   = None
    from_cache:     bool              = False
    error:          Optional[str]     = None           # graceful degradation flag

    def to_json(self) -> str:
        d = asdict(self)
        return json.dumps(d)

    @classmethod
    def from_json(cls, data: str) -> "NewsData":
        d = json.loads(data)
        d["articles"] = [NewsArticle(**a) for a in d["articles"]]
        return cls(**d)


@dataclass
class SentimentResult:
    overall_label:      str                             # positive/neutral/negative
    overall_score:      float                           # weighted confidence
    positive_count:     int     = 0
    neutral_count:      int     = 0
    negative_count:     int     = 0
    article_count:      int     = 0
    analysis_time_ms:   Optional[float] = None
    error:              Optional[str]   = None


@dataclass
class ResearchReport:
    symbol:             str
    generated_at:       str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    stock:              Optional[StockData]      = None
    news:               Optional[NewsData]       = None
    sentiment:          Optional[SentimentResult]= None
    llm_summary:        Optional[str]            = None
    llm_risks:          Optional[str]            = None
    llm_positives:      Optional[str]            = None
    llm_outlook:        Optional[str]            = None
    total_time_ms:      Optional[float]          = None
    errors:             List[str] = field(default_factory=list)
