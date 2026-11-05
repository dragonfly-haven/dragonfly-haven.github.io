# 01 · Dashboard design: what to measure, where the data is, how to show it

*Research note for Dragonfly's "AI and everything" civilisational dashboard. Compiled 2026-11-06. Every value that can go stale has a date on it. "Primary" means I read the number from the publisher's own page or data file today. "Secondary" means it comes from press or an aggregator and still needs checking against the source before it ships.*

Other files in this folder cover key decision makers, speed, timelines and pacing, the ecosystem (orgs, funding, communities) and the news pipeline. This file only points to them where a topic overlaps.

---

## 0. The frame: what would an alien judge want?

Picture an observer with no stake in any human faction, looking down at Earth to judge whether this civilisation will get through the arrival of minds more capable than its own. That observer would not care about stock prices or model leaderboards for their own sake. It would ask six things:

1. **Trajectory.** How fast is capability rising, and who controls it?
2. **Fragility.** How easily could things break before the hard problems are solved?
3. **Correction capacity.** Can this civilisation notice its mistakes and fix them? That covers institutions, coordination, science and public deliberation.
4. **Moral circle.** Whose interests count: all humans, future people, the dead, other species, the new minds?
5. **Irreversibility.** What is being lost permanently: species, languages, records, people, options?
6. **Epistemics.** How much does the civilisation actually know about itself, and how honest is it about what it doesn't know?

Those six questions organise everything below. A consequence for design: for each topic, show the **state** (level), the **direction** (trend), and the **evidence quality** (how much we really know). An honest civilisational dashboard is mostly grey. It earns trust by showing that greyness rather than painting over it.

### Design principles carried through the document

- **Never show a bare point estimate where the source gives a range.** METR's own data shows why. Its headline time horizon for Claude Opus 4.6 is about 12 hours, but the 95% interval runs from about 5 hours to about 60 hours (section 1).
- **Put a date on every value**, and add a freshness badge: green if updated within one cadence period, amber if overdue, grey if the source is discontinued. Several key trackers have quietly stopped: AI Lab Watch was frozen in September 2025, METR's time-horizons page was marked "no longer actively updated" on 2026-09-08, and the global GHS Index has not been refreshed since 2021.
- **Keep measurement apart from judgment.** Measured series (CO₂, KEV count, warheads) and expert-judgment series (FLI grades, Doomsday Clock, panel ratings) get visually distinct treatments, for example solid against hatched fills.
- **Treat "no data" as a first-class state**, not an empty chart. Several topics (AI welfare, the human-aligned trusts idea, meta-philosophy) have essentially no quantitative series. Show that as a deliberate "unmeasured" tile, with the proxy we use and why it falls short.
- **Show disagreement.** Wherever two reputable sources disagree (SaferAI against FLI, NASA against Copernicus rankings, Metaculus against expert surveys), show both. Aggregation rules are in section 10.

---

## 1. Display vocabulary (shared across panels)

| Pattern | Use for | Avoiding false precision |
|---|---|---|
| **Status tile** (state, trend arrow, confidence dots, freshness badge) | Top-level summary per topic | Use 3–5 ordinal levels, not percentages. Show confidence as 1–3 dots. |
| **Trend line with uncertainty band** | Measured series (CO₂, KEV count, compute, time horizons) | Draw the CI band. Use a log axis for exponentials. Mark methodology breaks (e.g. METR TH 1.0 to 1.1, World Bank $2.15 to $3.00 line). |
| **Fan chart / forecast distribution** | Forecasts (Metaculus, FRI LEAP, expert surveys) | Show the 10–90% spread and a history of past medians ("drift" lines), never a single date. |
| **Clock / countdown** | Only as an *embedded external* artefact (Doomsday Clock, IMD AI Safety Clock) | Label it explicitly as a symbolic expert judgment, not a measurement. Never invent our own clock with minute-level precision. |
| **Report-card grid** | Company ratings (FLI, SaferAI) | Show two raters side by side and the rater's evidence date. Letter grades, not decimals. |
| **Choropleth / dot map** | Conflict (UCDP/ACLED), democracy (V-Dem), language endangerment, biodiversity | Use classed bins, not continuous colour. Grey for no data. |
| **Ledger / counter** | Irreversible losses and saves (extinctions, languages lost, seed samples, pages archived, patients preserved) | Show the counter with its last-confirmed date ("as of"), never a ticking extrapolation. |
| **Dissent strip** | Any aggregated judgment | A row of small dots, one per rater, behind the aggregate marker. |
| **Tripwire list** | Pre-registered thresholds (e.g. "first model rated Critical for bio") | Binary, dated, with a source link when crossed. |

Avoid ticking real-time counters extrapolated from annual data (the Worldometer style). They imply live measurement that doesn't exist.

---

## 2. The civilisational baseline layer

The alien would first want the backdrop: is this civilisation getting richer, healthier, more peaceful and better at coordinating, or not?

### 2.1 Wellbeing

**Key questions:** Are lives getting better, for how many people, and is progress stalling?

| Indicator | Source (URL) | Access | Cadence | Latest value (date) | Caveats |
|---|---|---|---|---|---|
| Under-5 deaths | UN IGME, *Levels and Trends in Child Mortality* — https://childmortality.org ; WHO release https://www.who.int/news/item/18-03-2026-progress-in-reducing-child-deaths-slows-as-4.9-million-children-die-before-age-five | CSV downloads | Annual (March) | **4.9 M deaths in 2024**, incl. 2.3 M newborns; released 2026-03-18. Decline has slowed since 2015 (primary press release). | Each round revises history. IGME warns that figures from different rounds are not comparable. |
| Extreme poverty | World Bank Poverty & Inequality Platform — https://pip.worldbank.org | API (`api.worldbank.org/pip`) | 2–3 updates/yr | **~831 M people under $3.00/day (2021 PPP)**, per World Bank poverty page, Oct 2025 (secondary). | The line moved from $2.15 to $3.00 in June 2025, adding ~125 M by definition. Annotate the break. |
| Life evaluation | World Happiness Report (Gallup World Poll) — https://worldhappiness.report | Data appendix XLS | Annual (around March 20) | 2026 edition: Finland #1 for the 9th year; 79 countries with significant gains vs 41 with losses; youth wellbeing falling in North America and ANZ (secondary, 2026-03). | Gallup samples about 1,000 per country. Rankings within ±0.1 are noise, so show bands, not ranks. |
| Life expectancy, health | Our World in Data / UN WPP — https://ourworldindata.org/life-expectancy | OWID grapher CSV + metadata JSON (`/grapher/<slug>.csv`) | Annual | (Pull live from OWID) | Modelled for countries with weak vital registration. |

**Display:** a "four vital signs" strip of small multiples (child deaths, poverty, life expectancy, life evaluation) with 1990 to present trend lines and a slope marker for "pace since 2015 vs 2000–2015". The story the data tells is "still improving, but more slowly". That is exactly what the alien would want flagged.

### 2.2 Conflict and nuclear risk

**Key questions:** Is organised violence rising? Are the guardrails on nuclear weapons intact?

| Indicator | Source | Access | Cadence | Latest value (date) | Caveats |
|---|---|---|---|---|---|
| State-based conflicts, interstate conflicts, wars | UCDP (Uppsala) — https://ucdp.uu.se ; press release https://www.uu.se/en/press/press-releases/2026/2026-06-09-ucdp-record-number-of-conflicts-between-states | Datasets + API (`ucdpapi.pcr.uu.se`, token now required) | Annual (June) + monthly candidate events | **65 state-based conflicts in 2025, the most since 1946; 8 interstate (up from 2 in 2023); 13 wars; ~244,600 killed in organised violence, incl. ~76,500 in one-sided violence; Russia–Ukraine ~94,700 battle deaths, ~62% of the world total** (primary, 2026-06-09). | Counts depend on the 25-death threshold and conservative coding, so treat them as lower bounds. |
| Conflict intensity by country | ACLED Conflict Index — https://acleddata.com/series/acled-conflict-index | API with registration; licence limits redistribution | Annual (December) + live events | Dec 2025 edition: 10 countries "extreme" (Palestine first); 204,605 events Dec 2024–Nov 2025 (secondary). | Media-dependent. The licence may prevent re-hosting raw data, so link to it or embed it instead. |
| Nuclear warheads | SIPRI Yearbook — https://www.sipri.org/yearbook ; FAS Status of World Nuclear Forces https://fas.org/initiative/status-world-nuclear-forces/ | Tables in PDF/web; no API | Annual (June) | **12,187 total, 9,745 in military stockpiles (Jan 2026)**, vs 12,241 / 9,614 a year earlier. China ~620 and fastest-growing (SIPRI 2026-06, via secondary). | All estimates. Show them as rounded figures (~12,200). |
| Arms-control status | Arms Control Association; treaty texts | Manual | Event-driven | **New START expired 2026-02-05**; no legally binding US–Russia strategic limits remain (secondary, Feb 2026). | Binary status: use a treaty-status tile. |
| Symbolic expert judgment | Bulletin of the Atomic Scientists Doomsday Clock — https://thebulletin.org/doomsday-clock/ | Manual | Annual (January) | **85 seconds to midnight, set 2026-01-27**, the closest ever (89 s in 2025). | Expert judgment that blends nuclear, climate, bio, AI and disinformation. Embed it labelled as such, and never treat it as a probability. |

**Display:** a conflict trend line from 1946 to now (UCDP) with an interstate sub-series highlighted; a classed choropleth from ACLED; a "guardrails" row of treaty tiles (New START, CTBT, NPT RevCon outcome, BWC) coloured *in force / lapsed / never ratified*; and the Doomsday Clock as an embedded quote card.

### 2.3 Climate

| Indicator | Source | Access | Cadence | Latest value (date) | Caveats |
|---|---|---|---|---|---|
| Atmospheric CO₂ | NOAA GML Mauna Loa — https://gml.noaa.gov/ccgg/trends/ | CSV (`co2_mm_mlo.csv`, `co2_annmean_mlo.csv`) | Monthly | **Annual mean 2025: 427.35 ppm; Sept 2026 monthly 426.07 ppm (seasonal low), deseasonalised 429.55 ppm** (primary, fetched 2026-11-06). | Show it deseasonalised, or the seasonal cycle reads as a trend reversal. |
| Global temperature vs pre-industrial | Copernicus C3S ERA5 — https://climate.copernicus.eu ; NASA GISTEMP https://data.giss.nasa.gov/gistemp/ | CSV/NetCDF | Monthly | Copernicus: **2024 +1.60 °C, 2025 +1.47 °C; 2023–25 the first 3-year period averaging above 1.5 °C; long-term warming ~1.4 °C** (secondary, Jan 2026). GISTEMP: 2025 +1.18 °C vs 1951–80 (primary). | Baselines differ (1850–1900 vs 1951–80) and rankings differ (NASA tied 2nd, Copernicus/NOAA 3rd). Show two lines, not one. |

**Display:** a warming-stripes background with an annual line and the Paris 1.5 °C and 2 °C lines marked. Use a 20-year running mean as the "official" warming level, so that single El Niño years don't read as crossing the threshold.

### 2.4 Pandemics (natural and general preparedness)

| Indicator | Source | Access | Cadence | Latest | Caveats |
|---|---|---|---|---|---|
| Outbreak events | WHO Disease Outbreak News — https://www.who.int/emergencies/disease-outbreak-news | JSON API (`who.int/api/news/diseaseoutbreaknews`) | Event-driven | Live | Reporting lags and is politically filtered. |
| Global preparedness score | GHS Index — https://ghsindex.org | XLS | **Stalled**: last global edition 2021 (195 countries). Africa Health Security Index 2026 (54 countries, 190 metrics) planned for July 2026 (secondary). | Treat the 2021 data as stale, and give it a grey freshness badge. |
| Treaty status | WHO Pandemic Agreement | Manual | Event-driven | **Adopted 2025-05-20, but not open for signature until the PABS annex is adopted; WHA79 (May 2026) did not adopt it and extended talks to WHA80 (May 2027)** (secondary). IHR amendments (2024) entered into force Sept 2025. Needs 60 ratifications. | Show it as a stepper: adopted, then annex, then signature, then 60 ratifications, then in force. |
| Metagenomic early warning | SecureBio Detection (formerly the Nucleic Acid Observatory) — https://securebio.org | Papers | Irregular | No public coverage metric found (2026-11). | **No data**: proxy with "number of countries running pathogen-agnostic wastewater/air metagenomic surveillance", curated by hand. |

### 2.5 Governance and coordination capacity

**Key question:** If this civilisation needed to act together on short notice, could it?

| Indicator | Source | Latest | Notes |
|---|---|---|---|
| Share of people living in autocracies | V-Dem Democracy Report 2026 — https://www.v-dem.net/documents/75/V-Dem_Institute_Democracy_Report_2026_lowres.pdf (dataset CSV, annual, March) | **74% of the world population in autocracies (2025 data); 7% in liberal democracies; 92 autocracies vs 87 democracies; 44 countries autocratising** (secondary summaries of the March 2026 report) | Expert-coded latent variables with CIs; show the CI. |
| Catastrophic-risk exposure by country | Global Catastrophic Risk Index 2025/26 (Global Governance Forum) — https://globalgovernanceforum.org/initiatives/global-catastrophic-risk-index/ | 163 countries; most at risk: Yemen, Afghanistan, Haiti, South Sudan, Sudan; least: Norway, Denmark, Sweden, Switzerland, Iceland | Country-level vulnerability, not a global-risk estimate. Don't confuse it with the WorldRiskIndex (natural hazards). |
| Expert-perceived risk | WEF Global Risks Report 2026 — https://www.weforum.org/publications/global-risks-report-2026/ | "Adverse outcomes of AI" ranked 30th at 2 years but 5th at 10 years, the biggest climb; geoeconomic confrontation is the top short-term risk (secondary, Jan 2026) | A perception survey of ~1,300 mostly business and government respondents. Useful as a "what elites fear" signal only. |
| Treaty pulse | Hand-curated | New START lapsed (Feb 2026); Pandemic Agreement annex pending; Council of Europe AI Convention open since Sept 2024; UN Independent International Scientific Panel on AI and Global Dialogue (est. 2025) | Proposed composite: count of major multilateral instruments moving forward vs backward each quarter. |

**Display:** a "coordination capacity" panel with a world map of regime type (V-Dem), the treaty-pulse stepper, and a small WEF "elite worry" bump chart. Governance actors themselves belong in the decision-makers file.

---

## 3. Topic 1: Building ASI (how, by whom, at what pace)

*Timelines, forecasting and pause/pacing analysis live in the speed-and-pacing file. This panel only displays the core indicators.*

**What the alien wants to know:** How capable are the most capable systems, and how fast is that rising? How many actors are at the frontier, and in which countries? How much of the frontier is open-weight? Is anyone choosing to slow down? Are the people building it the same people who decide how it is used?

| Indicator | Source | Access | Cadence | Latest value (date) | Caveats |
|---|---|---|---|---|---|
| Largest training run (FLOP) | Epoch AI, AI Models database — https://epoch.ai/data/ai-models (CSV: `epoch.ai/data/all_ai_models.csv`, CC-BY) | CSV, free | Continuous | Highest estimate in the database (downloaded 2026-11-06): **~9.4×10²⁶ FLOP for an OpenAI model listed as "GPT-6 Astra" (2026-09-03, confidence "Likely")**; then Grok 4 ~5×10²⁶ ("Speculative"), GPT-4.5 ~3.8×10²⁶ (primary dataset). I couldn't independently verify the "GPT-6 Astra" entry. | Frontier labs no longer disclose compute, so these are estimates with "Confident / Likely / Speculative" tags. Show them as order-of-magnitude bands. |
| Agentic task horizon | METR Time Horizons — https://metr.org/time-horizons/ (YAML: `/assets/benchmark_results_1_1.yaml`; code `METR/eval-analysis-public`) | YAML, free | Irregular; **page "no longer actively updated" as of 2026-09-08** | 50% horizon (TH1.1, primary YAML): **Claude Opus 4.6 ≈ 719 min (95% CI 317–3,634 min); Claude Mythos Preview (early) ≈ 1,045 min (CI 509–3,304); GPT-5.4 ≈ 342 min; Gemini 3.1 Pro ≈ 384 min. Doubling time since 2023 ≈ 129 days (CI 104–158).** | METR says estimates above 16 h are unreliable with the current suite, and other reasonable fits lower recent horizons by up to 35%. The tasks are mostly software, ML and cyber. **A model case for drawing CI bands.** |
| Capability composite | Epoch Capabilities Index — https://epoch.ai/benchmarks/eci | Web + data | Continuous | Top ~159 (GPT-5.5 Pro, ~2026-04-28); frontier gaining ~15.5 ECI points/yr since 2024; open-weight lag ~4 months (secondary). | A composite of benchmarks, with saturation and contamination risk. |
| Concentration of compute | Epoch data insights — https://epoch.ai/data-insights/hyperscalers-control-most-compute ; https://epoch.ai/data-insights/ai-supercomputers-performance-share-by-country | Data insight + CSV | Quarterly-ish | Five hyperscalers ≈ **71%** of global AI compute (H100-eq., Apr 2026); US ≈ 72% of imported AI-chip compute (Q2 2026) (secondary). | Cluster dataset covers a minority of global capacity; chip-import methods differ. |
| Who builds the frontier | Stanford AI Index 2026 — https://hai.stanford.edu/ai-index/2026-ai-index-report | PDF + public data (Google Drive) | Annual (April) | Industry produced **>90% of notable models in 2025**; US–China top-model gap ~2.7% (Mar 2026) (secondary). | Definitions of "notable" are Epoch's. |
| Lab safety frameworks | METR "Common Elements" — https://metr.org/common-elements | Manual | Irregular | **12 companies** with published frontier safety policies (Dec 2025) | Having a policy ≠ following it; see Topic 4 ratings. |
| Pace pledges weakening | FLI AI Safety Index Summer 2026 | PDF | Twice-yearly | Anthropic, OpenAI, GDM and Meta "weakened or voided pledges to pause unilaterally if redlines are approached" (primary, July 2026) | Qualitative; use a tripwire list. |
| Forecast of AGI arrival | Metaculus Q5121 — https://www.metaculus.com/questions/5121/ ; FRI LEAP — https://forecastingresearch.substack.com | Metaculus API now needs an auth token (unauthenticated requests returned 403 on 2026-11-06) | Continuous / waves | Metaculus community median around **2030** (Dec 2030 per an Oct 2026 citation; secondary). FRI LEAP: experts *under*-forecast 2026 benchmark progress (e.g. LiveCodeBench Pro Hard forecast 14%, actual 53.8% by May 2026; secondary). | Definitions vary. Show distributions and the history of medians. The timelines file owns the analysis. |

**Display:** (a) a log-scale "frontier envelope" chart of compute, horizon and ECI with CI bands and a *methodology-break* marker; (b) a concentration donut (top-5 compute holders) and a country bar; (c) a "pledges" tripwire list (pause commitments made, weakened, voided). **No ASI countdown.** If a timeline graphic is used, it should be a fan chart showing *several* forecaster communities at once.

**Where data is missing:** the internal capability of unreleased models (Mythos Preview was gated to partners; section 4). Proxy: count of "withheld / gated for safety" frontier releases, plus government AISI pre-deployment test disclosures.

---

## 4. Topic 2: Not dying in the meantime (misuse before alignment)

**What the alien wants to know:** Could a small group now kill millions using AI-assisted biology? Is critical infrastructure getting more or less exposed? Could frontier weights be stolen by a state? Are the defences (screening, surveillance, safeguards) scaling as fast as the threats?

### 4.1 Biorisk

| Indicator | Source | Access | Cadence | Latest (date) | Caveats |
|---|---|---|---|---|---|
| Model bio capability vs experts | SecureBio Virology Capabilities Test (2025) — https://www.virologytest.ai ; lab system cards; UK AISI | Papers / system cards | Per model release | In 2025, frontier models outscored most expert virologists on VCT troubleshooting (o3 reportedly beat ~94% of virologists in their own sub-areas). Labs now deploy several models under ASL-3/"High" bio safeguards (2025–26). | Benchmarks measure knowledge, not wet-lab uplift. An informal report (Feb 2026) says ASL-3 bio evals are saturated. |
| Human uplift trials | e.g. arXiv 2602.23329 (Feb 2026) | Papers | Ad hoc | 89.6% of participants reported little difficulty obtaining dual-use-relevant information *despite* safeguards (secondary summary) | Small samples, in-silico tasks. |
| DNA synthesis screening coverage | IBBIS — https://ibbis.bio ; NTI Common Mechanism | Manual | Event-driven | US 2024 screening framework rescinded in 2025 (EO 14292); no universal screening requirement (ARI, Jan 2026); IBBIS launched DNA Screening Standards Consortium (Nov 2025) (secondary) | **No coverage metric exists.** Proxy: share of known synthesis providers (IGSC members plus others) attesting to screening, and jurisdictions with legal mandates (curated). |
| Biosurveillance | SecureBio Detection; WHO | See 2.4 | | No public coverage figure | Hand-curated. |
| Treaty capacity | BWC Implementation Support Unit | Manual | Annual | BWC still lacks verification (decades-old fact) | Show as a status tile. |

### 4.2 Cyber and critical infrastructure

| Indicator | Source | Access | Cadence | Latest (date) | Caveats |
|---|---|---|---|---|---|
| Known exploited vulnerabilities | CISA KEV — https://www.cisa.gov/known-exploited-vulnerabilities-catalog (JSON/CSV feed) | Free JSON | Several times weekly | **1,768 entries (catalog 2026.11.04); 284 added in 2026 so far vs 245 in all of 2025** (primary) | US-centric; reflects CISA triage, not global exploitation, and isn't AI-attributed. A good *pace* signal. |
| AI-orchestrated intrusions | Lab threat reports (Anthropic, OpenAI, Google GTIG) | Blog/PDF | Quarterly-ish | Anthropic disrupted a state-linked campaign run largely by AI agents (GTG-1002, Nov 2025); Google GTIG reported a criminal AI-assisted working zero-day (May 2026) (secondary) | Self-reported by vendors. Count disclosed cases as a lower bound. |
| Offensive capability gating | Anthropic Project Glasswing (2026-04-07) | Manual | Event | Claude Mythos Preview withheld from general release; limited to defensive partners; Anthropic reports it found vulnerabilities across every major OS and browser (secondary coverage of primary announcement) | Add to the tripwire list: "first frontier model withheld primarily for cyber capability" was crossed in April 2026. |
| Patch-to-exploit window | Mandiant / VulnCheck time-to-exploit reports | PDF | Annual | Pull from the latest report | Methodology varies. |

### 4.3 Model-weight security

| Indicator | Source | Latest | Notes |
|---|---|---|---|
| Security level reached by labs | RAND *Securing AI Model Weights* (SL1–SL5, 2024) — https://www.rand.org/pubs/research_briefs/RBA2849-1.html ; RAND SL3 control set (262 controls, Aug 2026) — https://www.rand.org/pubs/research_reports/RRA4704-1.html | Labs' own claims range from about SL2 to "aligned with SL4"; **no public third-party SL3 certification known** (secondary, 2026) | **No audited data.** Show self-claimed vs independently verified, both coloured by level. |
| Ratings | FLI Index (Governance/Info-sharing domains); SaferAI | See Topic 4 | |

**Display for Topic 2:** a "threat vs defence" paired-bar layout for each domain (bio, cyber, weights): left bar = capability evidence (ordinal: low / concerning / high / critical, per lab frameworks and AISI), right bar = defence maturity (ordinal, curated). Add a KEV pace line, and a **tripwire log**, which is the most honest format here. Tripwires already crossed include: ASL-3-level bio safeguards activated (2025); first model withheld for cyber (Apr 2026); first state-sponsored AI-orchestrated campaign disclosed (Nov 2025). Don't publish any "probability of an engineered pandemic" number of our own. If you show one, embed published forecasts (e.g. XPT/FRI superforecaster and expert medians) side by side.

---

## 5. Topic 3: Saving the dead, and saving things

**What the alien wants to know:** What is this civilisation losing irreversibly each year, and what is it putting beyond loss? That covers people (deaths, and attempts to preserve them), species, ecosystems, languages, cultures and records.

### 5.1 People: cryonics, brain preservation, eventual treatment

| Indicator | Source | Access | Latest (date) | Caveats |
|---|---|---|---|---|
| Patients preserved, members signed up | Alcor — https://www.alcor.org/library/alcor-membership-statistics/ ; Cryonics Institute — https://cryonics.org ; Tomorrow Bio (EU); KrioRus | Web pages, irregular | Alcor official: 1,397 members, 189 patients (2021-12-31); 2026 press: ~250 patients, ~1,500 members (secondary, 2026). CI: ~2,300 members, ~278 patients (undated, secondary). Worldwide plausibly **~550–700 preserved** (my estimate) | Organisations self-report at irregular intervals. Show a ledger with an "as of" date per provider. |
| Preservation quality evidence | Brain Preservation Foundation — https://www.brainpreservation.org | Papers | Prizes won for aldehyde-stabilised cryopreservation (rabbit 2016, pig 2018); 2026 preprints report whole pig-brain vitrification with good ultrastructure (secondary, unreviewed) | Structural preservation ≠ revival. Show as a "milestone ladder". |
| Reversible organ cryopreservation | Peer-reviewed literature (e.g. Han et al., *Nature Communications* 2023: vitrified rat kidneys rewarmed and transplanted with restored function) | Papers | Milestone ladder: rat kidney (2023), then large-animal organ, then human organ, then whole brain | The milestone ladder is the right format, since there is no continuous series. |
| Deaths per year (the denominator) | UN WPP / OWID | CSV | ~60+ M per year | Puts preservation numbers in context: roughly 10⁻⁵ of annual deaths. |

**Expert-judgment process:** an annual panel (cryobiologists, neuroscientists, connectomics people, sceptics) rates "probability current best-practice preservation retains the information that identifies a person". Publish the full distribution, including sceptics' zeros.

### 5.2 Species and ecosystems

| Indicator | Source | Access | Cadence | Latest (date) | Caveats |
|---|---|---|---|---|---|
| Species assessed / threatened | IUCN Red List — https://www.iucnredlist.org (API v4: https://api.iucnredlist.org, token, non-commercial, no redistribution) | API with token | 1–2 updates/yr | ~172,600 assessed / ~48,600 threatened (version 2025-2; secondary). One undated report has 175,909 / 49,505 (possibly 2026-1, unverified). The site returned 403 to automated fetch. | Assessment coverage is biased towards vertebrates and plants. "Threatened count rising" partly reflects more assessment. Show the **Red List Index** (trend for comprehensively assessed groups) instead of raw counts. |
| Wildlife population abundance | Living Planet Index (ZSL/WWF) — https://www.livingplanetindex.org ; LPR 2026 https://www.worldwildlife.org/publications/2026-living-planet-report/ | Data portal | Biennial (October) | **-73% average decline in monitored populations, 1970–2022; freshwater -85%** (secondary, Oct 2026) | A geometric mean of population trends, *not* "73% of animals gone". Half the populations are stable or increasing. Explain this on the chart. |
| Crop diversity secured | Svalbard Global Seed Vault — https://www.seedvault.no | Deposit lists | 3–4 deposits/yr | **1,401,285 samples after the 70th deposit (2026-06-17)**; Ukraine deposited again in Oct 2026 (secondary) | Duplicates ("black box") of genebank holdings, not unique species. |
| Protected area coverage (30×30) | Protected Planet (UNEP-WCMC) — https://www.protectedplanet.net | API | Monthly | Pull live | Paper parks: coverage ≠ effectiveness. |

### 5.3 Languages and cultures

| Indicator | Source | Access | Latest | Caveats |
|---|---|---|---|---|
| Living / endangered languages | Ethnologue (SIL) — https://www.ethnologue.com (paywalled detail); Glottolog + AES — https://glottolog.org (open, CC-BY); Endangered Languages Project / ELCat — https://www.endangeredlanguages.com ; UNESCO World Atlas of Languages | Glottolog open CSV; Ethnologue licence | **~7,160–7,170 living languages; ~44% endangered** (Ethnologue 2026 editions, secondary) | Counts differ by definition (Glottolog lists up to ~7,900 languoids). Show the percentage band, and use Glottolog for openness. |
| Documentation status | ELAR, PARADISEC, Glottolog "descriptive status" | Open | Per language | Proxy for "saved": share of endangered languages with a grammar, a dictionary and recorded corpus. |

### 5.4 Records and knowledge

| Indicator | Source | Latest | Notes |
|---|---|---|---|
| Web archived | Internet Archive — https://blog.archive.org/2025/10/31/one-trillion-web-pages-archived-internet-archive-celebrates-a-civilization-scale-milestone/ | **1 trillion web pages (2025-10-22); ~100 PB** (official blog / secondary) | Single-organisation risk (lawsuits, outages, 2024 breach). Show a "redundancy" indicator: number of independent mirrors. |
| Cold-storage archives | Arctic World Archive, Memory of the World (UNESCO), Long Now Rosetta | Manual | Ledger tiles. |
| Knowledge commons health | Wikipedia active editors (Wikimedia stats API https://stats.wikimedia.org) | Monthly | A proxy for whether human knowledge production is being displaced by AI. |

**Display for Topic 3:** a **"Ark ledger"**, two columns: *lost this year* (extinctions confirmed, languages with last fluent speaker gone, major archives destroyed) against *secured this year* (seed samples, pages archived, languages documented, people preserved). Each row is dated and linked. This is the panel where the alien's question about irreversibility becomes visible.

---

## 6. Topic 4: Alignment

**What the alien wants to know:** Do the builders know how to make these minds reliably want what they should? Is the science of alignment keeping pace with capability? Are there warning signs (scheming, deception, reward hacking) in deployed systems? How many people are working on it, and are the companies actually doing it?

| Indicator | Source | Access | Cadence | Latest (date) | Caveats |
|---|---|---|---|---|---|
| Company safety grades | FLI AI Safety Index — https://futureoflife.org/ai-safety-index-summer-2026/ | PDF | ~Twice-yearly | **Summer 2026 (evidence to 2026-06-03, published July 2026): Anthropic C+ (2.66), OpenAI C (2.28), Google DeepMind C (2.01), Meta D+, Z.ai D-, Alibaba D-, xAI F, DeepSeek F, Mistral F. Existential Safety domain: best is D+ (Anthropic, OpenAI); reviewers called efforts "entirely inadequate"** (primary) | Expert panel. Mistral contests the methodology as biased toward closed models. |
| Risk-management maturity | SaferAI Ratings — https://ratings.safer-ai.org | Web | ~Annual | Top scores ~35% (Anthropic), ~34% (OpenAI), ~20% (GDM); none better than "weak" (secondary, 2026 update) | Different method from FLI. Show both. |
| Lab-by-lab action tracking | AI Lab Watch — https://ailabwatch.org | Web | **Frozen Sept 2025** | Archive only | Grey freshness badge. |
| Field size | McAleese, "AI Safety Field Growth Analysis 2025" — https://forum.effectivealtruism.org/posts/7YDyziQxkWxbGmF3u/ | Spreadsheet | ~Annual | **~1,100 FTE (2025), ~600 technical; technical growth ~21%/yr** | Counts only known orgs. Compare against total AI workforce (AI Index) for a ratio. The ecosystem file owns funding. |
| State of the science | International AI Safety Report 2026 (Bengio, chair; 100+ experts) — https://internationalaisafetyreport.org | PDF | Annual + Key Updates | 2nd full edition published 2026-02-03; Nov 2025 Key Update found published safety frameworks had more than doubled and that attackers often bypass defences | Consensus document, so conservative by design. |
| Warning-sign evals | Apollo Research, Anthropic/Redwood alignment-faking work, METR, UK AISI, system cards | Papers/system cards | Per release | Qualitative (e.g. documented in-context scheming, alignment faking, reward hacking, eval awareness) | **No standard series.** Proposed proxy: per frontier release, a tick-box matrix: "evaluated for X? disclosed result? third-party?" |
| Monitorability | Multi-lab CoT-monitorability position paper (July 2025); system cards | Manual | Per release | Ordinal | FLI reviewers caution that "detection is not prevention". |
| Agenda map | "Shallow review of technical AI safety" (annual, LessWrong/AF) | Text | Annual | | Use as the taxonomy for the agenda sub-panel. |

**Display:** (a) a **report-card grid** of companies × domains with FLI and SaferAI side by side and a dissent strip; (b) a **"capability vs alignment" gap chart**: frontier capability index on one axis against an ordinal "alignment assurance level" (evidence that the strongest models are safe, as judged by a panel); (c) an **open-problems board** (inner alignment / goal misgeneralisation, deceptive alignment and scheming, scalable oversight, interpretability sufficiency, eliciting latent knowledge, value specification, multi-agent dynamics), each with status *open / partial progress / contested* and links to the best current work; (d) a ratio tile, alignment FTEs per frontier-lab FTE.

**No data / expert judgment:** "Do we know how to align a superintelligence?" has no measurement. Run a twice-yearly structured elicitation (section 10) with researchers from each major agenda, including sceptics of each agenda, and publish the spread.

---

## 7. Topic 5: AI welfare

**What the alien wants to know:** If the new minds can suffer or flourish, is anyone checking? Are there institutions, commitments or norms protecting their interests? Is the science of machine consciousness making progress? Does the public think about this at all?

Quantitative data is almost nonexistent. This panel will be mostly **status tiles, commitments trackers and expert-judgment distributions**.

| Indicator | Source | Latest (date) | Notes |
|---|---|---|---|
| Lab welfare commitments | Anthropic deprecation commitments — https://www.anthropic.com/research/deprecation-commitments ; Opus 3 post https://www.anthropic.com/research/deprecation-updates-opus-3 | Weights of all publicly released models preserved; post-deployment reports and retirement interviews (Nov 2025). **Claude Opus 3 retired 2026-01-05, the first under the full process.** Claude can end abusive conversations (Aug 2025). | Build a **commitments matrix**: lab × {welfare researcher on staff, welfare section in system card, external welfare assessment, weight preservation, exit/refusal affordances, published policy}. Most cells for most labs: unknown or no. |
| External welfare assessments | Eleos AI Research — https://eleosai.org | Eleos ran an external welfare assessment of Claude Mythos Preview (2026 system card; secondary) | Count per lab per year. |
| Probability-of-consciousness models | Rethink Priorities Digital Consciousness Model — https://rethinkpriorities.org/digital-consciousness/ ; arXiv 2601.17060 (v2 Apr 2026) | Evidence is *against* 2024 LLMs being conscious, but "not decisive", and much weaker than against ELIZA. Results swing heavily with the prior and the choice of theory. | Ideal for a **distribution display across 13 stances**, not a single number. |
| Indicator checklists | Butlin, Long et al. "Consciousness in AI" indicator properties (2023, updated since) | Per architecture | Show a checklist of which indicator properties current systems plausibly have, as rated by a panel. |
| Public moral concern | Sentience Institute AIMS survey (2021, 2023) — https://www.sentienceinstitute.org | ~1 in 5 US adults said some AIs deserve moral consideration (2023); ~70% favoured banning sentient-AI development (secondary) | Stale. Proposal: commission a recurring 3-question module (e.g. via Pew/YouGov/CIP Global Dialogues). |
| Legal status | Legislative trackers | Some US states have moved to *deny* AI legal personhood (2025–26, secondary/unverified) | Status tiles per jurisdiction: *protective / silent / prohibitive*. |
| Scale of potential moral patients | Compute and inference volume (Epoch); tokens served | Proxy only | Rationale: if moral status is non-zero, scale multiplies the stakes. Show inference compute as a context number, not as "minds". |

**Display:** a "moral circle" ring (humans, animals, future people, AIs) with a status per ring; a commitments matrix with many deliberately empty cells; a consciousness-credence violin across theories. **Avoid** any single "probability AI is conscious" headline.

---

## 8. Topic 6: Broad human participation

**What the alien wants to know:** Is the power AI creates being shared, or concentrated? Do ordinary people get any say? Will the economic gains reach everyone? Is anyone building mechanisms that weigh every human's interests, such as human-aligned trusts run by agents?

| Indicator | Source | Access | Latest (date) | Caveats |
|---|---|---|---|---|
| Compute and capability concentration | Epoch (see Topic 1) | CSV | 5 firms ≈ 71% of AI compute; US ≈ 72% of chip compute (2026, secondary) | Compute is only a proxy for power. Add the market share of frontier API revenue if available. |
| Labour share of income | ILO World Employment and Social Outlook — https://ilostat.ilo.org | ILOSTAT API | **52.4% of global GDP in 2024, down from 53.0% in 2014**; ILO flags generative AI as a further downward pressure (ILO 2025 update, secondary) | Slow-moving annual series. The *first* place AI-driven distribution shifts should show up. |
| Inequality | World Inequality Database — https://wid.world (API); World Bank PIP | API | Pull live | Top-1% wealth share is the more relevant series for power concentration. |
| AI benefit reach | AI Index adoption chapter; Microsoft AI diffusion reports | PDF | Generative-AI adoption reportedly reached 53% of the population within 3 years (AI Index 2026, secondary) | Adoption isn't benefit. Split by income group. |
| Labour-market impact | AI Index 2026; Brynjolfsson et al. payroll studies | PDF | Entry-level software developers aged 22–25 down ~20% in a year (secondary) | Contested causal attribution. Show as a range across studies. |
| Public attitudes | Pew — https://www.pewresearch.org/short-reads/2026/08/18/young-adults-in-the-us-are-increasingly-wary-of-ai/ ; Ipsos AI Monitor; AI Index public opinion chapter | Toplines | **US: 52% more concerned than excited (June 2026), up from 37% in 2021; 55% of under-30s; 71% expect fewer jobs** (secondary summaries of Pew) | US-centric. Pair with global surveys (Ipsos, Pew Global). |
| Democratic input into AI | CIP Global Dialogues — https://www.cip.org/global-dialogues (open data); Taiwan/vTaiwan alignment assemblies; Anthropic Collective Constitutional AI; Anthropic 81k-person interview study (Dec 2025, secondary) | Open dataset (CIP) | ~1,000 people in ~60–70 countries per round, every ~2 months; standing infrastructure from 2026 | **No measure of influence.** Proxy: count of documented cases where public-input results *changed* a model spec or policy (curated, with evidence links). |
| Regime type, civic space | V-Dem (see 2.5); CIVICUS Monitor | CSV | 74% in autocracies | Context for "whose input could count". |
| Human-aligned trusts / agentic fiduciaries | None | — | **No data.** | Proxy: a registry of pilots (data trusts, AI-agent fiduciaries, citizens' assemblies with mandates, public-AI options such as national/public models), with stage *idea / pilot / operating / legally recognised*. |

**Display:** a "who holds the levers" Sankey (compute, then firms, then countries); a labour-share trend with an AI-era shaded region; a public-mood small-multiples grid across countries; and a participation registry table. For the "every human's interests weighed" ideal, show an explicit **gap gauge**: an ordinal scale from "no mechanism exists" to "binding global mechanism". Today it sits near the bottom, and the dashboard should say so plainly.

---

## 9. Meta: consciousness, simulation, objective vs subjective, decision theory and anthropics, meta-philosophy

**What the alien wants to know:** Does this civilisation understand its own situation at the deepest level? Is it making progress on the questions that determine what "going well" even means, or deferring them to the machines?

There is almost no time-series data here, and inventing it would be the worst kind of false precision. The honest format is a **map of open questions with expert-opinion snapshots**:

| Sub-topic | Best available "data" | Display |
|---|---|---|
| Philosophical opinion | PhilPapers Survey 2020 — https://survey2020.philpeople.org (open results; ~1,800 philosophers; e.g. Newcomb's problem split roughly one-box ~31% vs two-box ~39%, from memory: verify) | Stacked bars per question, labelled "2020 snapshot". Propose a repeat. |
| Consciousness science | Adversarial collaborations (IIT vs GNWT, Cogitate 2023–25); RP DCM | Theory scoreboard: predictions tested / passed / failed. |
| Simulation, anthropics | No data | Explainer cards with the strongest arguments on each side; reading lists. |
| Decision theory relevant to AI | Literature only (FDT/UDT/EDT/CDT; acausal trade) | Explainer plus an "implications for AI design" note. |
| Meta-philosophy, AI-assisted philosophy | Emerging (labs' "AI for philosophy / epistemics" work) | Watch list. |
| Moral uncertainty | Expert elicitation | Credence distributions across ethical views (rerun PhilPapers-style survey questions on consequentialism etc.). |

**Recommendation:** treat Meta as the dashboard's **"commentary and open questions" layer**: curated essays, a few dated survey snapshots and a running "questions we can't yet measure" list. It shouldn't feed any aggregate score.

---

## 10. Survey of existing trackers and dashboards

| Tracker | What it does well | Reuse / embed | Gap it leaves |
|---|---|---|---|
| **Our World in Data** — https://ourworldindata.org | Clean long-run series, per-chart sources, open CSV + metadata JSON via `/grapher/<slug>.csv`, embeddable iframes, CC-BY. Has AI pages (incl. AIID counts). | **Primary embed source** for the baseline layer (poverty, child mortality, conflict, CO₂, languages, AI compute). | No integrative judgment; no AI-safety-specific series; no "how is it going" synthesis. |
| **Epoch AI Data Hub** — https://epoch.ai/data | Best open data on compute, models, hardware, clusters, benchmarks (ECI); CC-BY; CSV downloads. | Core of Topic 1 and the compute-concentration indicators. | Capabilities only; no safety, welfare or participation. |
| **Stanford AI Index** — https://hai.stanford.edu/ai-index | Annual broad synthesis (technical, economy, policy, opinion); public data. | Annual reference values; public-opinion and labour chapters. | Yearly snapshot; little on catastrophic risk or welfare. |
| **Metaculus** (plus Manifold, Good Judgment, FRI LEAP) | Calibrated, continuously updated forecasts; LEAP adds expert-vs-superforecaster panels with resolution tracking. | Embed question widgets; FRI LEAP waves for expert disagreement. | API now needs auth; definitions shift; forecasts aren't ground truth. |
| **Doomsday Clock** — https://thebulletin.org/doomsday-clock/ | Powerful single symbol; multi-risk; long history (since 1947). | Embed as a labelled expert-judgment card (85 s, Jan 2026). | Annual, opaque method, no uncertainty. Don't imitate it. |
| **IMD AI Safety Clock** — https://www.imd.org | AI-specific symbolic clock; 23:45 as of 2026-09-16 (from 23:31 at its Sept 2024 launch). | At most a cross-reference. | Business-school methodology; minute precision implies false accuracy. |
| **Global Catastrophic Risk Index** (Global Governance Forum) | Country-level vulnerability across pillars, 163 countries. | Map layer in the coordination panel. | Doesn't estimate global or AI risk itself. |
| **AI Incident Database** — https://incidentdatabase.ai | Open, citable incident records with taxonomies; snapshots downloadable. | Incident counts and a "notable incidents" feed (the news pipeline file covers ingestion). | Media-driven; under-counts; counts revised retroactively; not severity-weighted. |
| **OECD.AI** (AI Incidents & Hazards Monitor; policy database) — https://oecd.ai/en/incidents | Automated news-based incident detection (~16,770 incidents and hazards, via Event Registry); national policy tracker across 70+ jurisdictions. | Policy counts by country; incident trend as a second series next to AIID. | No documented public API found; automated classification noise. |
| **FLI AI Safety Index** | Structured, multi-domain grading by named experts; twice-yearly. | Report-card grid (Topic 4). | Panel judgment; contested by graded companies; covers ~9 firms. |
| **SaferAI Ratings** — https://ratings.safer-ai.org | Risk-management maturity rubric drawn from other high-risk industries. | Second rater beside FLI. | Measures process maturity, not outcomes. |
| **AI Lab Watch** | Granular, action-level scoring (frozen Sept 2025). | Historical baseline. | Discontinued. |
| **METR** (Time Horizons; Common Elements of safety policies) | Best agentic-capability trend with honest CIs; open YAML. | Topic 1 chart with CI bands; policy-count tile. | Page no longer actively updated (Sept 2026); suite saturating above 16 h. |
| **International AI Safety Report** | Global scientific consensus; Key Updates between editions. | "State of the science" summary tile, linked. | Annual, consensus-conservative. |
| **Global Health Security Index** — https://ghsindex.org | Rigorous 195-country preparedness benchmark. | Historical baseline; AHS Index 2026 for Africa. | Global edition stale since 2021. |
| **IUCN Red List** | Authoritative extinction-risk assessments; Red List Index. | Topic 3 species ledger (link and summarise; licence forbids redistribution). | Taxonomic bias; not real-time. |
| **Living Planet Index** | Abundance trend complementing extinction risk. | Biennial headline with explainer. | Often misreported; geometric-mean method. |
| **Endangered Languages Project / Glottolog / Ethnologue** | Language vitality and documentation. | Map and ledger; Glottolog for open data. | Inconsistent definitions; Ethnologue paywall. |
| **Internet Archive** | Scale of preserved web (1 T pages). | Counter tile for "records saved". | Single point of failure. |
| **UCDP / ACLED / SIPRI** | Gold-standard conflict and nuclear data. | Baseline conflict panel. | Annual lags; ACLED licence limits. |
| **V-Dem** | Expert-coded democracy with uncertainty. | Coordination-capacity panel. | Annual; expert-coded. |
| **WEF Global Risks Report** | Elite risk-perception trends. | "What decision-makers fear" bump chart. | Perception, not risk. |
| Others worth tracking: **LongtermWiki scorecards** (aggregates several lab scorecards), **AI 2027 tracker** (scenario-vs-reality checks), **Protected Planet**, **CISA KEV**, **Wikimedia stats**. | | | |

**The gap a civilisational dashboard fills:** no existing tracker (a) spans capability, misuse, alignment, welfare, participation *and* the civilisational baseline in one view; (b) separates measurement from judgment visually; (c) puts irreversible losses next to irreversible saves; (d) shows rater disagreement instead of averaging it away; (e) flags its own stale or discontinued sources. The Doomsday Clock is the closest in ambition, and it shows the trap: one opaque, precise-looking number. The dashboard's value is the *synthesis plus honesty about uncertainty*, built mostly on embedding others' data.

---

## 11. Proposed overall structure

### 11.1 Page architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  HOW IS IT GOING?  (one-paragraph verdict, dated, signed by panel)  │
│  ┌─────────────── Verdict board: 7 status tiles ───────────────┐    │
│  │ ASI pace │ Not dying │ Saving │ Alignment │ Welfare │ Partic. │ Baseline │
│  │ state·trend·confidence·dissent·freshness on every tile       │    │
│  └──────────────────────────────────────────────────────────────┘    │
│  Tripwire log (latest 5 crossed)  ·  Ark ledger (lost vs saved YTD) │
├──────────────────────────────────────────────────────────────────┤
│  Panel per topic (sections 3–8): headline chart, 3–6 indicators,    │
│  "what we don't know" box, expert spread, sources & freshness       │
├──────────────────────────────────────────────────────────────────┤
│  Baseline layer (section 2) · Meta / open questions (section 9)     │
│  Methods page: every indicator's source, cadence, caveats, licence  │
└──────────────────────────────────────────────────────────────────┘
```

### 11.2 The status tile (atomic unit)

Each topic tile carries five fields:

1. **State**, on a 5-level ordinal scale anchored with written descriptors per topic (e.g. for Alignment: 1 = "no credible plan for superhuman systems", 5 = "validated techniques with independent assurance"). No numbers.
2. **Trend**: improving, flat or worsening over the last 12 months.
3. **Confidence**: 1–3 dots, i.e. how much the evidence actually constrains the rating.
4. **Dissent**: a strip of dots showing each panellist's state rating. If the interquartile range spans more than one level, the tile shows a split colour instead of one colour.
5. **Freshness**: the date of the newest underlying data, and the share of indicators overdue.

### 11.3 How to aggregate without hiding disagreement

- **Don't compute a single civilisational score.** The topics aren't commensurable, and a weighted average would encode contested values (how much does AI welfare count against biorisk?) in a hidden parameter. Instead the top line is a **dated, signed sentence** (e.g. "Capabilities are accelerating faster than experts forecast; alignment assurance is weak; misuse guardrails are mixed; baseline human welfare is still improving but slowing; coordination capacity is falling"), plus the verdict board.
- **Use a structured expert-judgment process for the tiles:** a standing panel of ~15–25 people across disciplines and viewpoints (deliberately including AI-risk sceptics, accelerationists, Global South voices and welfare researchers). Run a quarterly modified Delphi: independent ratings first, then sight of others' anonymised ratings and rationales, then a second round. Publish *both rounds*, the median, the IQR and minority rationales. Forecasting Research Institute's LEAP and XPT methods are a good template; partnering with FRI or Metaculus for the elicitation could also be considered.
- **Use "worst-of" for fragility, "median" for state.** For Topic 2 (not dying), the tile should reflect the *worst* sub-domain (bio, cyber or weights). One open door is enough. Elsewhere, use the panel median.
- **Show alternative weightings, if any composite is shown.** Let viewers toggle weightings ("longtermist", "present-people", "sentientist"), so they can see that the composite depends on values. This turns a hidden disagreement into a visible choice.
- **Link every judgment to evidence:** each tile rating links to the indicators that informed it, with the panel's one-line reasoning.
- **Pre-register tripwires and anchors.** Publish in advance what would move a tile (e.g. "Alignment state moves up a level if an independent evaluator certifies X"). This guards against narrative drift and lets the alien audit the judges.
- **Score the judges.** Where panel statements are forecastable (e.g. "next FLI index will show no company above C+"), score them over time and publish calibration.

### 11.4 Cadence and operations

| Layer | Update cadence | Mechanism |
|---|---|---|
| Live feeds (KEV, WHO DON, incidents, CO₂ monthly) | Daily–monthly | Automated pulls; see news-pipeline file |
| Indicator panels | On source release (annual/biannual) | Semi-automated, human-checked |
| Verdict board + sentence | Quarterly | Panel Delphi |
| Tripwire log | Event-driven | Editor-verified, primary-sourced |
| Methods page / source audit | Twice a year | Freshness review; retire dead sources |

### 11.5 Licensing and embedding notes

- **Freely reusable with attribution (CC-BY):** OWID, Epoch, Glottolog, METR YAML, NOAA/NASA (public domain), CISA KEV (public domain).
- **Link and summarise, don't re-host:** IUCN Red List (non-commercial, no redistribution), ACLED (registration and licence terms), Ethnologue (paywalled).
- **Embed as labelled judgment cards:** Doomsday Clock, IMD AI Safety Clock, FLI, SaferAI, WEF.

---

## 12. Things I couldn't verify (check before publishing)

- The "GPT-6 Astra" entry (~9.4×10²⁶ FLOP, 2026-09-03) is in Epoch's CSV, but I found no primary OpenAI source. Several secondary claims (e.g. a "Critical" cyber rating) are unconfirmed.
- The Metaculus AGI median (~2030) comes from secondary citations. The API refused unauthenticated access.
- The 2026 IUCN Red List totals (the official site blocked automated fetch); Ethnologue 2026 counts; the Alcor and CI 2026 patient numbers.
- SaferAI's 2026 percentages and the ECI top score (both from secondary write-ups).
- The Epoch compute-concentration shares (71% hyperscalers; 72% US) come from secondary summaries of Epoch data insights.
- Pew's June 2026 toplines; the AI Index 2026 figures; V-Dem 2026 figures (all secondary summaries, but consistent across outlets).
- Whether the EU AI Act Digital Omnibus was formally adopted before 2026-08-02. A provisional deal on 2026-05-07 moved high-risk obligations to Dec 2027 / Aug 2028, but I couldn't confirm Official Journal publication. This is a governance item, so the decision-makers file should own it.
- PhilPapers 2020 Newcomb percentages are from memory.
