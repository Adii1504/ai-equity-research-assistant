# 🗓️ Fingo — 18-Day Sprint Plan & Task Distribution

> **Project**: Fingo — AI-Powered Micro-Enterprise Lending Companion  
> **Problem Statement**: SIH 2026 — 26092 (Avoiding delayed disbursements)  
> **Team Size**: 6 people  
> **Duration**: 18 days  
> **Modules**: 8  
> **Goal**: Fully working demo — Web + Android APK, all modules integrated, voice agent operational

---

## 📦 The 8 Modules

| # | Module | Complexity | Dependencies |
|---|--------|-----------|--------------|
| M1 | Frontend + Mobile (Android/Capacitor) | High | Needs API contracts from Backend |
| M2 | Geo-Spatial Layer (NPA-Filtered Map) | Medium-High | Needs Backend routes + NPA data |
| M3 | Backend (FastAPI Core + DB Pipelines) | High | Foundation — everything depends on this |
| M4 | Module 1: Feasibility Engine | Medium | Needs Backend routes + demographics data |
| M5 | Module 2: Financial Calculator + AA Handoff | Medium | Needs Backend routes + AA mock data |
| M6 | Module 3: Scheme Engine / Router | Medium | Needs Financial Calculator output |
| M7 | AA Form + Database Connection Pipelines | Medium | Needs DB schema from Backend |
| M8 | Voice Agent | Medium | Needs all modules working (last to integrate) |

---

## 🔗 Dependency Map

```
Day 1-2:  Backend (M3) defines API contracts + DB schema FIRST
              ↓
Day 3+:   Everything starts in parallel
              ├── Frontend (M1) builds UI pages against API contracts
              ├── Geo-Spatial (M2) builds map + NPA filter
              ├── Feasibility (M4) builds LLM engine
              ├── Financial Calc (M5) builds calculator + AA mock
              ├── Scheme Engine (M6) builds matching logic
              └── DB Pipelines (M7) builds models + migrations
              ↓
Day 13+:  Voice Agent (M8) integrates on top of working modules
              ↓
Day 15+:  Mobile (M1) wraps everything in Capacitor
              ↓
Day 16-18: Integration testing, polish, demo prep
```

> **Critical**: P1 (Backend Lead) is the bottleneck for the first 2 days. API contracts and DB schema must be delivered before anyone else can start building against real endpoints. After Day 2, all 6 people work in parallel.

---

## 👥 Team Roles & Module Ownership

| Person | Role | Modules Owned | Why This Pairing |
|--------|------|---------------|------------------|
| **P1** | Backend Lead & Architect | M3 (Backend Core) | Defines the contracts everyone builds against. The glue of the team. |
| **P2** | Frontend Lead | M1 (Frontend + Mobile) | Dedicated UI person. Makes everything look polished. Starts Capacitor on Day 11. |
| **P3** | Geo-Spatial + Voice Specialist | M2 (Geo-Spatial) + M8 (Voice Agent) | Both involve external API integrations (maps, speech-to-text). |
| **P4** | AI / LLM Engineer | M4 (Feasibility Engine) | Deep prompt engineering + structured LLM output parsing. Needs focus. |
| **P5** | Financial Engine Developer | M5 (Calculator + AA) + M7 (DB Pipelines) | Calculator and AA are tightly coupled — AA data feeds into the FOIR computation. |
| **P6** | Scheme & Data Engineer | M6 (Scheme Router) + Dossier Generator + Seed Data | Scheme matching flows directly into Dossier generation. Also owns all seed/demo data. |

---

## 📅 Three-Phase Timeline

### Phase 1: Foundation (Day 1–6)

**Goal**: Backend skeleton done. All modules have working standalone logic.

### Phase 2: Core Build (Day 7–12)

**Goal**: All modules connected via API. Frontend talks to backend. Data flows end-to-end. First APK built.

### Phase 3: Integration & Polish (Day 13–18)

**Goal**: Voice works. Android polished. Demo rehearsed. Backup video recorded.

---

## 📋 Day-by-Day Task Breakdown

### P1 — Backend Lead & Architect

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Define ALL API contracts (OpenAPI spec) for every module | `docs/api_spec.md` — every endpoint, request/response schema |
| 2 | DB schema design + SQLAlchemy models + migrations | `models/` — User, Partner, Scheme, FeasibilityReport, Dossier tables |
| 3 | FastAPI server skeleton — all new route stubs with mock responses | `web/server.py` — everyone can now hit real endpoints |
| 4 | Wire Financial Calculator endpoint (connect P5's engine) | `/api/calculator` returns real results |
| 5 | Wire Feasibility endpoint (connect P4's engine) | `/api/feasibility` returns real results |
| 6 | Wire Geo-Spatial endpoint (connect P3's locator) | `/api/geo/partners` returns real results |
| 7 | Wire Scheme Router endpoint (connect P6's engine) | `/api/schemes/match` returns real results |
| 8 | Wire AA Handoff endpoint (connect P5's AA module) | `/api/aa/analyze` returns real results |
| 9 | Wire Dossier endpoint (connect P6's generator) | `/api/dossier/generate` returns PDF |
| 10 | Integration testing — hit every endpoint E2E | All routes return correct data, errors handled |
| 11 | Redis caching for all new endpoints | Cached responses for demo stability |
| 12 | Auth integration — JWT on all new routes | Protected endpoints, user sessions work |
| 13 | Voice Agent API wiring (connect P3's voice module) | `/api/voice/process` routes to correct module |
| 14 | Load testing + edge case fixes | System handles 10 concurrent users |
| 15 | Pre-generate 5 demo datasets (cache feasibility reports) | Demo locations ready, zero live API risk |
| 16 | Code freeze — bug fixes only | Stable backend |
| 17 | Full team: End-to-end demo walkthrough. Record backup video. | — |
| 18 | Full team: 3× dry runs. Final bug fixes. Slides finalized. | — |

---

### P2 — Frontend Lead

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Study existing UI (`index.html`, `app.js`, `style.css`). Plan new page layouts. | Wireframes/sketches for 4 new pages |
| 2 | Build Calculator page UI (`calculator.html` + `calculator.js`) | Input form, live calculation display, EMI chart |
| 3 | Build Feasibility page UI (`feasibility.html` + `feasibility.js`) | Location picker, business type selector, report accordion |
| 4 | Connect Calculator UI to real `/api/calculator` endpoint | Calculator works end-to-end |
| 5 | Connect Feasibility UI to real `/api/feasibility` endpoint | Feasibility report renders from live API |
| 6 | Build Dossier page UI (`dossier.html` + `dossier.js`) | PDF preview, "Submit to SCA" button, download link |
| 7 | Build AA Consent flow UI — DPDP consent modal | Consent popup → loading state → results display |
| 8 | Connect Dossier + AA pages to real endpoints | Dossier generation works, AA flow works |
| 9 | Navigation overhaul — add all new pages to sidebar/nav | Consistent navigation across all pages |
| 10 | Mobile-responsive CSS for all new pages | Every page looks good on phone screen |
| 11 | Capacitor init — `npx cap init`, add android platform | Android project created |
| 12 | Capacitor build — first APK, test on emulator | App opens on Android, all pages load |
| 13 | Fix Android-specific issues (GPS permissions, status bar, back button) | APK works on real device |
| 14 | Polish — loading spinners, error toasts, animations | UI feels professional |
| 15 | Signed APK build — release-ready Android APK | Installable APK for demo device |
| 16 | Dark mode / theme consistency pass | Consistent look across all pages |
| 17 | Full team: Demo walkthrough + backup video | — |
| 18 | Full team: Dry runs + final fixes | — |

---

### P3 — Geo-Spatial + Voice Agent Specialist

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Research Leaflet.js + OpenStreetMap + OSRM routing API | Working knowledge of map stack |
| 2 | Build `partner_locator.py` — Haversine distance calculation | Function: given lat/lng + radius → list of partners |
| 3 | Build `npa_filter.py` — Health Score calculation + filtering | Function: given partners → scored + filtered list |
| 4 | Build `route_optimizer.py` — OSRM routing proxy | Function: given origin + destination → route polyline |
| 5 | Build Map page UI (`geo.html` + `geo.js`) with Leaflet | Map renders with tile layer, GPS/manual location input |
| 6 | Add NPA-colored markers to map (green/yellow/red) | Markers show Health Score in tooltip |
| 7 | Add routing line to map (draw path to healthiest bank) | Click a green marker → route appears |
| 8 | Connect map to real `/api/geo/partners` endpoint | Full geo pipeline works end-to-end |
| 9 | Offline tile caching for demo area (bundle tiles for demo location) | Map works even if WiFi drops during demo |
| 10 | Voice Agent: Research Web Speech API / Deepgram / Whisper | Pick the voice-to-text solution |
| 11 | Build voice capture module — mic button → transcribed text | User clicks mic, speaks, text appears |
| 12 | Build intent router — parse voice text → determine module | "I want to check my loan" → routes to Module 2 |
| 13 | Connect voice agent to Agent Orchestrator | Voice commands trigger real module actions |
| 14 | Test voice in multiple languages (Hindi, English at minimum) | Hindi voice input works |
| 15 | Polish — voice feedback UI (listening indicator, response readback) | Professional voice UX |
| 16 | Test voice on Android device (Capacitor mic permissions) | Voice works in APK |
| 17 | Full team: Demo walkthrough + backup video | — |
| 18 | Full team: Dry runs + final fixes | — |

---

### P4 — AI / LLM Engineer (Module 1: Feasibility Engine)

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Study existing `report_generator.py` — understand LLM call pattern | Full understanding of the pattern to clone |
| 2 | Collect + format demo demographics data (Census data for 5–10 blocks) | `feasibility/demo_demographics.json` |
| 3 | Build Market Reach Analyzer — population within radius + channels | Sub-prompt that generates market reach section |
| 4 | Build Opportunity & Niche Finder — cross-reference UDYAM data | Sub-prompt for opportunity analysis |
| 5 | Build SWOT Generator — budget-aware strengths/weaknesses | Sub-prompt for SWOT section |
| 6 | Build Threat Identifier — supply chain, seasonal, single-buyer risks | Sub-prompt for threats section |
| 7 | Build Competitor Mapper — density estimation from demographic data | Sub-prompt for competitor section |
| 8 | Build Product Market Value — optimal pricing + purchasing power | Sub-prompt for PMV section |
| 9 | Combine all 6 into `feasibility_engine.py` — single call → structured JSON | Complete feasibility report from one function call |
| 10 | Add 3 retries + fallback parsing (reuse `_parse_llm_response()` pattern) | Robust against LLM format variations |
| 11 | Pre-generate feasibility reports for 5 demo locations | Cached reports for demo stability |
| 12 | Test with different business types (dairy, tailoring, pappad, food stall, repair) | 5 different business types work correctly |
| 13 | Add PDF export for feasibility report (using fpdf2) | Download button generates clean PDF |
| 14 | Edge case testing — unknown locations, unusual business types | Graceful error handling |
| 15 | Performance optimization — report generates in < 10 seconds | Fast enough for live demo |
| 16 | Code freeze — only bug fixes | Stable module |
| 17 | Full team: Demo walkthrough + backup video | — |
| 18 | Full team: Dry runs + final fixes | — |

---

### P5 — Financial Engine Developer (Module 2: Calculator + AA + DB)

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Define financial formulas + edge cases | Formula spec document |
| 2 | Build `financial_calc.py` — Margin → Project Cost → Max Loan → EMI | Core calculator function |
| 3 | Add multi-tenure comparison (3yr, 5yr, 7yr side-by-side) | Calculator returns array of tenure options |
| 4 | Add subsidy calculation (PMEGP: 25%/35% based on category) | Effective loan and EMI after subsidy |
| 5 | Build `aa_handoff.py` — parse mock bank statement JSON | Extract: avg monthly income, existing EMIs, avg balance |
| 6 | Build FOIR calculation — `(Income × 50%) - Existing EMIs = Max EMI capacity` | Pre-approved ceiling computed from AA data |
| 7 | Build mock AA endpoint — realistic 12-month transaction data | `/api/aa/mock` returns sample bank statement |
| 8 | Build DPDP consent flow backend — consent token, timestamp logging | Consent recorded before AA data is fetched |
| 9 | Connect AA → Calculator pipeline — `Pre-Approved = Min(Margin-based, FOIR-based)` | Full AA-enhanced calculation works |
| 10 | DB pipeline — save calculation results, user sessions, consent logs | Data persists across sessions |
| 11 | Redis caching for calculator results | Instant recalculation on parameter change |
| 12 | Test with 10 different financial profiles | All edge cases handled |
| 13 | Add calculation audit trail — log every input/output | Explainability for judges |
| 14 | Integration test with Scheme Router (P6) | Calculator → Scheme Router pipeline works |
| 15 | Performance testing — calculator responds in < 500ms | Instant feel in UI |
| 16 | Code freeze | Stable module |
| 17 | Full team: Demo walkthrough + backup video | — |
| 18 | Full team: Dry runs + final fixes | — |

---

### P6 — Scheme & Data Engineer (Module 3: Scheme Router + Dossier + Data)

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Research all government schemes (PMEGP, MUDRA, Stand-Up India, PM Vishwakarma, DAY-NRLM, CGTMSE) | `schemes/scheme_data.json` — 30+ schemes with eligibility rules |
| 2 | Build scheme eligibility rules engine — category, age, loan amount, location matching | `scheme_router.py` — input profile → ranked scheme list |
| 3 | Add NPA-aware ranking — schemes offered by healthier banks rank higher | Scheme ranking considers bank health |
| 4 | Build `partners_seed.json` — 50+ partner bank branches with lat/lng, IFSC, NPA%, liquidity | Realistic demo data for geo module |
| 5 | Build `rbi_npa_data.json` — process RBI quarterly data into lookup table | NPA data ready for Health Score calculation |
| 6 | Build `dossier_generator.py` — auto-fill SCA application form | Given user + financial + scheme data → structured dossier |
| 7 | Build PDF generation using fpdf2 — professional SCA application layout | Clean, printable PDF with all sections |
| 8 | Add scheme comparison feature — side-by-side comparison of top 3 matches | UI-ready comparison data |
| 9 | Connect Dossier to Scheme Router — selected scheme auto-populates dossier | One-click from scheme selection to dossier |
| 10 | Connect Dossier to Financial Calculator (P5) — financial projections auto-populate | Dossier includes all financial data |
| 11 | Connect Dossier to Feasibility Report (P4) — business plan summary auto-populates | Dossier includes feasibility summary |
| 12 | Build mock SCA submission — success toast + Application ID | Demo-ready submission flow |
| 13 | Build `demo_demographics.json` — Census data for demo districts (help P4) | Demographics data for 5–10 blocks |
| 14 | Test full pipeline: Calculator → Scheme Match → Dossier → PDF → Submit | Complete dossier flow works E2E |
| 15 | Edge cases — no scheme matches, incomplete user data | Graceful handling |
| 16 | Code freeze | Stable module |
| 17 | Full team: Demo walkthrough + backup video | — |
| 18 | Full team: Dry runs + final fixes | — |

---

## 📊 Phase-by-Phase Grid View

### Phase 1: Foundation (Day 1–6)

| Day | P1 (Backend) | P2 (Frontend) | P3 (Geo+Voice) | P4 (Feasibility) | P5 (Calc+AA) | P6 (Scheme+Data) |
|-----|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | API contracts | Study existing UI | Research Leaflet | Study LLM pattern | Define formulas | Research schemes |
| 2 | DB schema + models | Calculator UI | Partner locator | Demographics data | Core calculator | Scheme rules engine |
| 3 | Server route stubs | Feasibility UI | NPA filter | Market Reach prompt | Multi-tenure calc | NPA-aware ranking |
| 4 | Wire Calculator | Connect Calc UI | Route optimizer | Opportunity prompt | Subsidy calc | Partner seed data |
| 5 | Wire Feasibility | Connect Feas UI | Map page UI | SWOT prompt | AA handoff parser | RBI NPA data |
| 6 | Wire Geo-Spatial | Dossier page UI | NPA markers on map | Threat prompt | FOIR calculation | Dossier generator |

**✅ Day 6 Checkpoint**: Every module should have a working standalone function callable from a Python shell.

---

### Phase 2: Core Build (Day 7–12)

| Day | P1 (Backend) | P2 (Frontend) | P3 (Geo+Voice) | P4 (Feasibility) | P5 (Calc+AA) | P6 (Scheme+Data) |
|-----|:---:|:---:|:---:|:---:|:---:|:---:|
| 7 | Wire Scheme Router | AA consent UI | Routing line on map | Competitor prompt | Mock AA endpoint | Scheme comparison |
| 8 | Wire AA endpoint | Connect Dossier+AA | Connect map to API | PMV prompt | Consent flow backend | Dossier→Scheme |
| 9 | Wire Dossier | Navigation overhaul | Offline tile cache | Combine 6 prompts | AA→Calc pipeline | Dossier→Calc |
| 10 | Integration testing | Mobile responsive CSS | Voice: research STT | Retries + fallback | DB pipelines | Dossier→Feasibility |
| 11 | Redis caching | Capacitor init | Voice: mic capture | Pre-gen demo reports | Redis caching | Mock SCA submit |
| 12 | Auth on new routes | First APK build | Voice: intent router | Test business types | Test 10 profiles | Demographics data |

**✅ Day 12 Checkpoint**: User can open web app → run calculator → see feasibility report → view map → generate dossier. Android APK should open and render all pages.

---

### Phase 3: Integration & Polish (Day 13–18)

| Day | P1 (Backend) | P2 (Frontend) | P3 (Geo+Voice) | P4 (Feasibility) | P5 (Calc+AA) | P6 (Scheme+Data) |
|-----|:---:|:---:|:---:|:---:|:---:|:---:|
| 13 | Voice API wiring | Android GPS fixes | Voice → Orchestrator | PDF export | Audit trail | Full pipeline test |
| 14 | Load testing | UI polish | Voice: Hindi test | Edge case testing | Integration w/ P6 | Edge cases |
| 15 | Pre-gen demo data | Signed APK | Voice: feedback UI | Performance opt | Performance test | Data validation |
| 16 | Code freeze | Theme consistency | Voice on Android | Code freeze | Code freeze | Code freeze |
| 17 | **FULL TEAM**: End-to-end demo walkthrough. Record backup demo video. | | | | | |
| 18 | **FULL TEAM**: 3× dry runs. Final bug fixes. Slide deck finalized. Demo device charged. | | | | | |

---

## 🔄 Daily Integration Checkpoints

| Day | Checkpoint | Who Tests |
|-----|-----------|-----------|
| 3 | Can we hit all API stubs and get mock responses? | P1 + P2 |
| 6 | Does the Calculator work end-to-end (UI → API → result)? | P2 + P5 |
| 9 | Does the full Feasibility flow work (input → LLM → rendered report)? | P2 + P4 |
| 12 | Does the map show NPA markers from the real API? Does the APK open? | P2 + P3 |
| 15 | Does the complete journey work? (Calc → Scheme → Dossier → PDF) | ALL |
| 17 | Full demo rehearsal on the actual demo device | ALL |

---

## ✅ Definition of Done (Per Module)

| Module | Done When... |
|--------|-------------|
| M1: Frontend + Mobile | All 4 new pages work on web + Android APK installs and runs on a real phone |
| M2: Geo-Spatial | Map shows NPA-colored markers, user enters location manually, routing line drawn to healthiest bank |
| M3: Backend | All new API endpoints return correct data, Redis cached, JWT protected, handles errors gracefully |
| M4: Feasibility | LLM generates all 6 sub-reports (SWOT, Market, Threats, Competitor, Opportunity, PMV) in < 10 sec |
| M5: Financial + AA | Calculator computes correct EMI, AA mock returns realistic data, FOIR ceiling calculated |
| M6: Scheme + Dossier | Scheme Router matches correctly, Dossier PDF generates with all sections auto-filled |
| M7: DB Pipelines | All data persists in PostgreSQL, consent logs saved, calculation audit trail works |
| M8: Voice Agent | User speaks in Hindi/English → correct module triggered → response displayed |

---

## 🧮 Key Formulas

### NPA Health Score
```
Health = (1 - NPA) × Liquidity

Thresholds:
  🟢 Green:  Health >= 0.75  (fast disbursement likely)
  🟡 Yellow: 0.60 <= Health < 0.75  (moderate risk)
  🔴 Red:    Health < 0.60  (excluded from route — high delay risk)
```

### Financial Structuring
```
Project Cost      = Available Margin / 0.10
Max Loan Amount   = Project Cost × 0.90
Monthly EMI       = [P × r × (1+r)^n] / [(1+r)^n - 1]

With AA Data:
  FOIR             = 50%
  Max EMI Capacity = (Verified Monthly Income × 50%) - Existing EMIs
  Pre-Approved     = Min(Max Loan, FOIR-Based Ceiling)
```

---

## ⚠️ Critical Rules

### 🔴 Non-Negotiable
- **Day 1-2 is P1's show.** Everyone else: research, collect data, build standalone functions. Use mock data until Day 3.
- **Do NOT start Capacitor/Android before Day 11.** Web app must be stable first.
- **Day 17-18 is sacred.** No new features. Only demo rehearsal, bug fixes, and backup video.

### 🟡 Daily Standup (15 min max)
Every morning, each person answers:
1. What did I finish yesterday?
2. What am I doing today?
3. Am I blocked on anything?

If someone is blocked, P1 (Backend Lead) unblocks them immediately.

### 🟢 Communication
- Use a shared group chat for quick questions
- Push code to the shared repo at least once per day
- Tag your commits with your person number: `[P3] Add NPA filter logic`

---

## 📁 New File Structure

```
aifinancecla/
├── geo/                              # M2: Geo-Spatial Module
│   ├── __init__.py
│   ├── partner_locator.py            # Haversine search, radius filter
│   ├── npa_filter.py                 # Health = (1-NPA) × Liquidity
│   ├── route_optimizer.py            # OSRM proxy
│   ├── partners_seed.json            # 50+ demo partners with NPA%
│   └── rbi_npa_data.json             # RBI quarterly NPA lookup
│
├── feasibility/                      # M4: Module 1
│   ├── __init__.py
│   ├── feasibility_engine.py         # 6 LLM sub-prompts → structured report
│   ├── market_data.py                # Static demographics loader
│   └── demo_demographics.json        # Census data for demo
│
├── calculator/                       # M5: Module 2
│   ├── __init__.py
│   ├── financial_calc.py             # Margin → Cost → Loan → EMI
│   └── aa_handoff.py                 # AA bank statement → dynamic ceiling
│
├── schemes/                          # M6: Module 3
│   ├── __init__.py
│   ├── scheme_router.py              # Eligibility matching + NPA ranking
│   └── scheme_data.json              # 30+ schemes with rules
│
├── dossier/                          # M6: Digital Dossier
│   ├── __init__.py
│   ├── dossier_generator.py          # Auto-fill + PDF generation
│   └── sca_mock.py                   # Mock SCA portal submission
│
├── voice/                            # M8: Voice Agent
│   ├── __init__.py
│   ├── voice_capture.py              # Speech-to-text
│   └── intent_router.py              # Parse intent → route to module
│
├── web/static/
│   ├── geo.html                      # Map + NPA-filtered partner locator
│   ├── geo.js                        # Leaflet + NPA marker logic
│   ├── feasibility.html              # Business feasibility report
│   ├── feasibility.js
│   ├── calculator.html               # Financial calculator + AA
│   ├── calculator.js
│   ├── dossier.html                  # Dossier preview + SCA submit
│   ├── dossier.js
│   └── ... (existing files unchanged)
│
├── mobile/                           # M1: Android
│   ├── capacitor.config.ts
│   └── android/
│
├── web/server.py                     # M3: MODIFIED — new routes added
├── docs/api_spec.md                  # API contracts (Day 1 deliverable)
└── SPRINT_PLAN.md                    # This file
```

---

*Last updated: September 2026*
