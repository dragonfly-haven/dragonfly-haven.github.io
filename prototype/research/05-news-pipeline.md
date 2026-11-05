# 05 — The news pipeline: sourcing, triage, judgement, summaries

*Research sketch for the Dragonfly "AI and everything" civilisational dashboard. Written 2026-11-06. Prices, API terms and product details go stale fast: each one carries the date it was checked, and anything I couldn't confirm from a primary source is marked **(unverified)**.*

---

## 0. The short version

- **The job is to decide what changes the verdict.** Picture an alien decision-maker looking down at Earth. It doesn't need everything that happened. It needs the few things that would change its judgement of how the planet is going, plus a reliable sense of what is drifting slowly underneath. The pipeline should be designed around that question rather than around volume or freshness.
- **Shape:** a three-stage funnel run with Claude. Haiku 5.5 does cheap relevance filtering of everything. Sonnet 5.5 scores and maps the surviving story clusters. Opus 5.5 verifies the top stories and drafts the briefs. A human editor approves anything that changes an indicator or leads a brief, through a GitHub pull request. The output is static JSON and HTML on GitHub Pages.
- **Cost:** model spend for a serious version is roughly **$150–450/month** at November 2026 prices (§6.3). Editorial time is the real cost: 30–60 minutes a day and 2–3 hours a week for one editor.
- **Hardest problems:** handling claims from interested parties (including Anthropic, whose models would do the judging), copyright limits on summarising, biosecurity infohazards, prompt injection hidden in fetched articles, and giving slow trends space next to breaking news.

---

## 1. Sources

### 1.1 Principles for choosing sources

1. **Primary before secondary.** For a civilisational lens the most valuable items are usually primary documents: a regulation in a gazette, a court filing, a preprint, a model or system card, a WHO Disease Outbreak News item, a dataset release. News articles are mainly useful as discovery signals and for context. The pipeline should always try to reach the primary document behind a story.
2. **Each topic needs its own source mix.** AI capabilities news comes first from lab blogs, arXiv and X. Biosecurity news comes from WHO, ProMED-style networks and bioRxiv. Language and species loss show up in slow databases, not news. Uniform generic news APIs will over-represent the AI-industry chatter that is easiest to scrape.
3. **Licence before scraping.** For every source, record the access method, the cost and what the terms allow us to *republish*. That last item is usually the binding constraint (§8.1).
4. **Diversify on purpose.** Use non-English sources (GDELT's machine translation helps), Global South outlets, and sources outside the AI-safety community. Otherwise the alien's view becomes a Bay Area view.

### 1.2 Source catalogue

Access details were checked on 2026-11-06 unless noted otherwise.

**General news firehoses**

| Source | What it gives | Access, cost, terms |
|---|---|---|
| **GDELT DOC 2.0 API** | Full-text search over worldwide online news in 65 machine-translated languages; timelines, tone, images | Free, no key. Rolling ~3-month search window ([GDELT launch post](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)). Third-party docs report about 1 request per 5 seconds **(unverified)**. Also: GDELT Events and GKG files every 15 minutes, and a BigQuery mirror. Good for discovery and for measuring coverage volume. Noisy; event coding is error-prone. |
| **Event Registry / NewsAPI.ai** | About 150k articles a day, clustered into events | Paid. This is what the OECD AI Incidents Monitor uses ([OECD AIM methodology](https://oecd.ai/en/incidents-methodology)). Worth pricing if GDELT proves too noisy. |
| **NewsAPI.org** | Headlines and article search | Free Developer tier is for development only, with about 24 h delay. Business tier is about $449/month for 250k requests, per third parties in mid-2026 ([apicostcalc](https://apicostcalc.com/newsapi.html)) **(unverified on newsapi.org)**. Probably not worth it at first. |
| **NewsData.io, Mediastack** | Cheaper news APIs | Low tens of dollars a month; commercial terms vary ([Geekflare 2026 roundup](https://geekflare.com/guides/global-news-api/)). Fallback options. |
| **Google News RSS** | Topic and search feeds | Terms limit it to personal, non-commercial display ([Google News terms](https://www.google.com/intl/en_us/terms_google_news.html)). Usable as a private discovery signal at most; don't republish anything from it. |
| **Common Crawl CC-NEWS** | Free WARC archive of news pages | Free. Useful for backfill and for building evaluation sets, not for live triage. |
| **Direct publisher RSS** | Reuters, AP, BBC, Al Jazeera, FT, The Economist, Nature News, Science, Carbon Brief, Rest of World, SCMP, The Hindu, and others | Free to *read*. Republication rights stay with the publisher. This is the bread-and-butter layer: around 150–300 hand-picked feeds. |

**AI frontier and labs**

| Source | Access |
|---|---|
| Lab blogs and news pages (Anthropic, OpenAI, Google DeepMind, Meta, xAI, Mistral, DeepSeek, Qwen/Alibaba, Moonshot, Zhipu), model and system cards, responsible-scaling and frontier-safety framework updates | RSS where it exists. Many lab pages have no feed, so monitor them with page-diffing (for example self-hosted [changedetection.io](https://github.com/dgtlmoon/changedetection.io)). Card and framework documents should be diffed, not just detected. A quiet edit to a safety framework is a real story. |
| Evaluators: METR, UK AI Security Institute, US CAISI, Apollo Research, Epoch AI | Blogs and RSS. Epoch's datasets are openly licensed and are a key input for the progress indicators (other researchers own those). |
| AI Incident Database; [OECD AIM](https://oecd.ai/en/incidents) | AIM classifies Event Registry news with a two-stage LLM pipeline and **does not independently verify** what it lists ([methodology](https://oecd.ai/en/incidents-methodology)). Treat it as a lead source. |
| GitHub releases of major open-weight models; Hugging Face trending | APIs, free. These pick up open-weight releases that never get a press release. |

**Research and preprints**

| Source | Access |
|---|---|
| **arXiv** (cs.AI, cs.LG, cs.CL, cs.CY, cs.CR, cs.MA; q-bio; physics.soc-ph) | RSS, the legacy API and OAI-PMH. Metadata is CC0. Terms require respecting rate limits; the commonly cited figure is 1 request every 3 seconds on a single connection ([arXiv API ToU](https://info.arxiv.org/help/api/tou.html)). A blog reports tighter limits from 2026-10-01 **(unverified)**. Use OAI-PMH for daily bulk pulls. Volume is high: several hundred new cs.AI/LG/CL papers a day. |
| **bioRxiv / medRxiv** | Free JSON API at api.biorxiv.org, no key. Has date-range "details" and "pubs" endpoints, the latter linking a preprint to its eventual journal version ([rOpenSci medrxivr docs](https://docs.ropensci.org/medrxivr/articles/medrxiv-api.html)). Page size is reported as 30 or 100, sources disagree **(unverified)**. |
| OpenAlex, Semantic Scholar, Crossref (including the Retraction Watch data) | Free or free with a key. Use them for citation velocity (a slow significance signal) and for **retraction monitoring**, so a story built on a paper can be revisited when the paper is retracted. |
| **LessWrong / Alignment Forum / EA Forum** | RSS (lesswrong.com/feed.xml with karma filters), a GraphQL API at /graphql, and per-post JSON routes on the Alignment Forum ([AF API notes](https://www.alignmentforum.org/api/SKILL.md)). Older GraphQL tutorials predate a schema change. Use a karma threshold plus curation status as a pre-filter. |

**Biosecurity and health**

| Source | Access |
|---|---|
| WHO Disease Outbreak News, WHO situation reports, ECDC weekly threats report, CDC HAN, Africa CDC | Free web and RSS. These are primary sources. |
| **BEACON** (Boston University) | Open-source outbreak intelligence that runs HealthMap signals through an LLM filter and then **expert verification before release** ([BU launch, Apr 2025](https://www.bu.edu/articles/2025/open-source-ai-infectious-diseases-monitoring-tool/)). This is the closest existing analogue to our triage design for one domain. |
| ProMED, CIDRAP, Johns Hopkins Center for Health Security, Nuclear Threat Initiative bio pages | ProMED moved behind a subscription a few years ago **(check current terms)**. CIDRAP is free. |
| Policy: federal and other legislative trackers for gene-synthesis screening rules, the BWC process, and so on | Via the governance sources below. |

**Conflict, security and nuclear**

| Source | Access |
|---|---|
| ACLED | Free with registration. Access caps and an authentication change (OAuth/cookie login replaced API keys from 2025-09-15) ([ACLED FAQ](https://acleddata.com/myacled-faqs)). Terms restrict redistribution of raw data. |
| UCDP, Crisis Group CrisisWatch (monthly), SIPRI, IAEA press, Bulletin of the Atomic Scientists | Free. Mostly slow-variable inputs. |

**Climate, environment and preservation**

| Source | Access |
|---|---|
| Copernicus C3S monthly climate bulletins, NOAA, Global Carbon Project, IPCC, Carbon Brief | Free. Mostly monthly or annual: slow variables with known release calendars. |
| IUCN Red List API, GBIF, Living Planet Index | Token, and generally non-commercial terms. Annual or periodic updates. |
| Languages: Glottolog, Endangered Languages Project, UNESCO; culture and knowledge: Internet Archive and Wikimedia blogs, UNESCO heritage in danger lists; seed banks (Svalbard deposit announcements) | Rarely "news"; mostly a calendar plus page monitoring. |
| Cryonics and biostasis: Alcor, Cryonics Institute, Tomorrow Bio, brain-preservation research (for example the Brain Preservation Foundation) | Blogs and page monitoring. Low volume. |

**Governance, regulators and courts**

| Source | Access |
|---|---|
| **US Federal Register API** | Free, no key, `federalregister.gov/api/v1/documents.json`. Two caveats: deep pagination misbehaves (out-of-range pages return page 1 with HTTP 200), so filter by agency and date ([Vaquill guide](https://www.vaquill.ai/blog/federal-register-api-python-search-rules-and-notices)). |
| regulations.gov, Congress.gov, GovInfo | Free with an api.data.gov key. |
| EUR-Lex / Official Journal, EU AI Office, European Parliament legislative observatory | RSS and SPARQL, free. |
| UK: GOV.UK per-organisation Atom feeds, legislation.gov.uk, Find Case Law (National Archives) | Free, mostly under the Open Government Licence. |
| China: CAC, MIIT, State Council notices | Mostly via translation intermediaries such as Stanford DigiChina and ChinAI (Jeffrey Ding). Note the dependence on intermediaries. |
| **CourtListener / RECAP** (US courts) | Free token, reportedly about 5,000 requests an hour authenticated **(unverified, from third-party pages)**. Docket alerts fire within seconds of new data, but coverage depends on what RECAP users have bought from PACER ([Free Law Project wiki](https://wiki.free.law/c/courtlistener/help/alerts/how-fast-are-courtlistener-alerts)). Key AI dockets to follow: NYT v. OpenAI, *Advance Local v. Cohere*, Musk v. OpenAI follow-ons, and any lab-versus-government cases. |

**Forecasting platforms** (used as a significance signal: a story that moves a well-traded forecast matters)

| Source | Access |
|---|---|
| **Metaculus** | API token required. Standard accounts see Community Prediction values on only about 50 questions. A bot-benchmarking tier sees about 250 open and 250 resolved. **Commercial use needs a written agreement** ([Metaculus OpenAPI spec](https://raw.githubusercontent.com/Metaculus/metaculus/main/docs/openapi.yml)). Ask for access as a non-profit early. |
| Manifold, Polymarket, Kalshi | Public APIs. Prediction-market prices can be manipulated and track what traders care about, so use them as one signal among several. |
| **Sentinel** weekly global-risks brief (xrisk.fyi) | A forecaster-written weekly brief with a colour status and forecasts ([Sentinel overview](https://forum.nunosempere.com/posts/GAFwc5jGFjqSetJiu/sentinel-early-detection-and-response-for-global)). Use it as a recall benchmark and a lead source, and credit it. |

**Social media**

| Source | Access |
|---|---|
| **X** | Since 2026-02-06, pay-per-use. Third parties report about $0.005 per post read with a monthly read cap; the $200/month Basic tier was retired, and remaining Basic subscribers were migrated from 2026-06-01 ([Open Terms Archive memo](https://opentermsarchive.org/en/memos/x-replaces-its-dollar200-entry-level-api-plan-with-a-pay-per-use-model/)) **(per-call rates unverified)**. Reading about 300 curated accounts at a few hundred posts a day costs tens of dollars a month. Still the fastest place AI news breaks. |
| **Bluesky** | Jetstream gives a free JSON firehose filterable by account and collection. It is live-only, with resumable cursors and a buffer of about 72 hours. Needs an always-on listener (a small VPS), not GitHub Actions. |
| Reddit, Hacker News, Mastodon | Hacker News (Firebase and Algolia APIs) is free and useful. Reddit's API has paid commercial terms. Mastodon is free per instance. |

**Newsletters** (for leads and recall checks, never for wholesale summarising; see §2)

Import AI, Transformer, AI Safety Newsletter (CAIS), Zvi Mowshowitz's weekly roundups, The Batch, ChinAI, Sentinel, Epoch's Gradient Updates, Interconnects, Understanding AI, and similar. Subscribe by email or RSS into a dedicated inbox. Their real value here is as a **recall test**: each week, check whether anything these editors led with was missing from our pipeline.

---

## 2. Comparable products and what to learn

| Product | What it does well | What it does badly, or doesn't fit | Lesson for us |
|---|---|---|---|
| **Import AI** (Jack Clark, weekly) | Paper-driven. Its "why this matters" framing turns a technical result into a judgement. Has a distinctive voice. | Single author. The author co-founded Anthropic and works there, which shows how interested-party authorship needs disclosure. | Every item should carry a one-line "why the alien cares". |
| **Transformer** (Shakeel Hashim and a small team, weekly briefing plus essays) | Strong on power and politics around AI. Original reporting. Broke down events like June 2026's government restriction of Fable well ([Transformer, 2026-06-19](https://www.transformernews.ai/p/fable-anthropic-trump-mythos-export-controls-white-house-amodei)). | Narrow by design: AI politics, mostly US and UK. | The governance and decision-makers lens; reporting beats aggregation when there is capacity. |
| **AI Safety Newsletter** (CAIS) | Short, readable, 2–3 stories per issue. Ran through 2026 (AISN #75 on 2026-06-17 covered Fable) ([archive](https://newsletter.safe.ai/archive)). | Irregular cadence. An advocacy organisation's view. | Depth on a few items beats a list of many. |
| **Zvi's weekly AI roundups** | Close to comprehensive. Sharp commentary. Quotes primary sources heavily. | Often well over 10k words a week. Comprehensive, but not digestible by a decision-maker. | The alien wants Zvi's *coverage* at a fraction of his *length*. That is the summarisation problem in one example. |
| **The Batch** (DeepLearning.AI) | Accessible. Industry and applications focus. | Light on risk. Upbeat by design. | A reminder that "AI news" defaults to the industry frame. |
| **Techmeme** | Since 2008 an algorithm ranks stories, by inbound links and age, and **human editors gate every top headline**. Shows story *clusters* with "more" links ([Nieman Lab, 2015](https://www.niemanlab.org/2015/09/techmeme-at-10-lessons-from-a-decade-in-the-aggregation-business/)). | Tech-industry centric. Link popularity favours the loud. | A hybrid where the machine proposes and a human disposes. The cluster as the unit. |
| **AINews** (smol.ai) | Fully LLM-generated daily recap of Discord, Reddit and X. Names the generating model. Publishes "not much happened today" issues honestly ([archive](https://buttondown.com/ainews)). | Insider chatter. Huge volume. No significance model beyond engagement and recency. | It's fine to say nothing important happened. Disclose model use. |
| **GDELT** | Global, multilingual, near-real-time. Measures coverage, not just content. | Very noisy. Machine-coded events misfire. | Use for discovery and blind-spot detection, never as a source of facts. |
| **Ground News** | Clusters each story and shows *who* covered it, with "Blindspot" reports for lopsided coverage ([methodology](https://ground.news/about-bias-ratings)). | Ratings are outsourced, per-outlet, and on a US left-right axis. Criticised for automation and for paywalling ratings. | Keep the blindspot idea but change its axis: geography, language, and insider versus outsider sources, not left versus right. |
| **Our World in Data** | Slow variables done properly: long time series, sourced, CC BY. Insists on "the world is awful, much better, and can be better" at the same time. | Not a news product. Updates are slow. | The indicator layer and the "what didn't make the news" framing. |
| **Metaculus** (news and question pages) | Ties news to forecasts. | API terms limit reuse (see above). | Use the change in a forecast as a measurable significance signal. |
| **Sentinel** | The closest analogue to the whole project: a weekly brief on global catastrophic risk with a status colour and calibrated forecasts. | Small team. Catastrophic-risk focus only, without the flourishing side. | Copy the status-level and forecast format. Use it for benchmarking. |
| **OECD AI Incidents Monitor** | An LLM pipeline at scale: a small model screens, a large model classifies, and the majority vote over a cluster's articles sets the label. | Explicitly doesn't verify. A fixed four-day article window splits slow-burning events. | The pipeline shape works, but verification must be a separate stage. |
| **BEACON** | LLM triage followed by expert sign-off before publishing. | Covers one domain. | The editorial gate is what makes it credible. |
| **Particle, Perplexity Discover** | Multi-source AI summaries per story. Particle links out prominently. | Perplexity was accused of copying exclusive and paywalled reporting with only footnote credit ([TechCrunch on Particle](https://techcrunch.com/2024/11/12/particle-launches-an-ai-news-app-to-help-publishers-instead-of-just-stealing-their-work)). | Credit the reporters and link out first. Summaries must not *substitute* for the original (§8.1). |
| **Wikipedia Current Events portal** | Neutral, terse, linked, volunteer-run. CC BY-SA. | No significance ranking. | A good model for the house style of the "what changed" log. |

**Overall pattern:** the strongest products have a clear editorial point of view and a human making the final call. The weak ones either chase volume or rank by engagement. None combines a *civilisational significance model* with a *standing set of indicators*. That combination is the gap Dragonfly could fill.

---

## 3. The triage pipeline

### 3.1 Units: item, cluster, thread, claim

- **Item:** one fetched document, such as an article, paper, filing or post. Carries its URL, source, fetch time, language, content hash and licence class.
- **Cluster:** items about the same event within a time window. This is the unit that gets scored.
- **Thread:** a persistent storyline that spans many clusters over weeks or months, for example "EU AI Act GPAI enforcement", "H5N1 in US dairy cattle", or "Fable restriction and aftermath". Threads let slow stories accumulate significance and keep the "what changed" log coherent. This fixes OECD AIM's split-event problem.
- **Claim:** an atomic assertion inside a cluster ("Lab X says model Y scores Z on benchmark W"), with who asserts it, their interest, and its evidence status. Most of the judgement work happens at the claim level.

### 3.2 Stages

```
 ingest ─► normalise ─► dedup ─► embed+cluster ─► S1 relevance (Haiku 5.5, batch)
                                                        │ ~10–20% pass
                                                        ▼
                              fetch full text / primary doc ─► S2 score+map (Sonnet 5.5)
                                                        │ tier ≥2
                                                        ▼
                         S3 verify + interested-party check (Opus 5.5) for tier ≥3
                                                        ▼
                    drafts: wire entries, indicator deltas, daily/weekly brief (Opus 5.5)
                                                        ▼
                         EDITOR: GitHub pull request review ─► merge ─► publish
```

**Normalise:** strip tracking parameters, resolve canonical URLs (`<link rel=canonical>`), detect language, extract the main text (trafilatura or similar), and record the licence class: *open* (CC, public domain, government), *link-only* (ordinary press), or *restricted* (paywall, or terms forbid reuse).

**Deduplicate (cheap, before any LLM):** first an exact URL and content hash, then MinHash or SimHash near-duplicate detection. This catches wire copy (AP and Reuters syndication) and press-release reprints. Keep every duplicate as an *item* in the cluster, because the *number and diversity* of independent outlets is itself a signal. Mark syndicated copies as not independent.

**Embed and cluster:** embed the title plus lede with a cheap embedding model. Anthropic has no embedding model of its own; Voyage's voyage-3.5-lite is $0.02 per million tokens with the first 200M free ([Voyage pricing](https://docs.voyageai.com/docs/pricing), checked 2026-11-06). Thousands of items a day cost cents. Cluster incrementally (cosine threshold within a 72-hour window, plus named-entity overlap). For borderline merges, ask Haiku "same event? yes/no/related" and attach "related" clusters to the same thread.

**S1, relevance filter (Haiku 5.5, Batch API):** title, lede and source go in. The output is a structured verdict: `{relevant: bool, topics: [...], reason}`. The prompt is generous (high recall). The question is only "could this plausibly matter to a civilisational observer under any of our topics?" Target pass rate: 10–20%. arXiv gets its own S1 prompt keyed to abstracts, with an extra filter for "is this a frontier capability, safety, alignment, welfare or biosecurity-relevant result?"

**S2, significance scoring and mapping (Sonnet 5.5):** runs per cluster, with full text of the 2–4 best items and the primary document if found. The output is a structured record (use structured outputs, `output_config.format`, with a JSON schema):

```
cluster_id, headline (neutral, ≤15 words), what_happened (2–3 sentences, factual),
topics[], indicators[{id, direction:+/−/?, est_magnitude, rationale}],
rubric{magnitude, irreversibility, breadth, novelty, leverage, evidence},
tier (0–4), claims[{text, asserted_by, interested_party:bool, interest, status}],
primary_doc_url, independent_sources_count, hype_flags[], infohazard_flag, why_alien_cares (1 sentence)
```

**S3, verification (Opus 5.5, high effort, tier ≥3 only, perhaps 10–40 clusters a day):** this is an adversarial pass. The model is told to *argue the story is less significant than S2 said*, then to reconcile. It checks each claim against the primary document. It checks dates (is this new, or a re-report of an old event? The BBC study below found assistants confuse current and archive material). It recomputes any number from the source text in a code step. It names what would falsify the story, and lists who has an interest in it being believed.

**Drafting (Opus 5.5):** produces wire entries, indicator-delta proposals, and the brief (§4). Everything is drafted *from the S2/S3 records*, not from raw articles. That keeps quoting and paraphrase minimal and the provenance chain intact.

### 3.3 The significance rubric

The guiding question for every cluster: **"If the alien missed this, how wrong would its picture of Earth's trajectory be in a year?"**

Score each dimension 0–5 against the anchors, then apply the evidence multiplier.

| Dimension | 0 | 3 | 5 |
|---|---|---|---|
| **M: Magnitude** (size of change to a tracked indicator) | No measurable change | Clear move in one indicator, within normal variance for a quarter | Step change, outside historical range |
| **I: Irreversibility / lock-in** | Easily undone (press release, proposal) | Sticky: enacted law, deployed infrastructure, signed contract | Effectively permanent: extinction, language death, weights released openly, catastrophe, entrenched power |
| **B: Breadth** | A niche or a single firm | A large country or sector, or a major ecosystem | Global; affects most humans or most future people |
| **N: Novelty / surprise** | Fully expected, already priced in | Ahead of or behind consensus timelines by months; moves a forecast 5–15 points | A forecast moves >15 points, or something no one predicted |
| **L: Leverage on the long-run trajectory** | No plausible effect on catastrophic or flourishing outcomes | Shifts the odds of a key transition (ASI governance, pandemic preparedness, alignment progress) modestly | Directly changes who controls ASI, how safely it is built, or whether a catastrophe happens |
| **E: Evidence multiplier** | 0.2: single interested-party claim or rumour | 0.6: credible report, one independent source, or a primary document not yet scrutinised | 1.0: primary document plus independent confirmation or replication |

**Score:** `S = E × (2L + I + M + B + N) / 6`, giving a range of 0–5. Leverage counts double because it is the alien's core concern.

**Tiers** (adjust the cut-offs during calibration):

| Tier | S | Treatment | Examples (illustrative, anchored) |
|---|---|---|---|
| **4: "wake the alien"** | ≥4.0 | Immediate wire entry. Editor paged. Leads the brief. Indicator updated after human sign-off. | Confirmed sustained human-to-human spread of a novel pathogen; nuclear use; a government seizing or withdrawing a frontier model (June 2026's Fable restriction would have scored around here once confirmed); a verified international compute or verification agreement; credible evidence of a frontier model sabotaging oversight in deployment. |
| **3: brief-lead** | 3.0–4.0 | Brief headline item. S3 verification. Indicator delta proposed. | Binding AI regulation entering into force; an independent eval showing a dangerous-capability threshold crossed; a major alignment or interpretability result replicated; a large conflict escalation; a record annual emissions or temperature datapoint. |
| **2: section item** | 2.0–3.0 | Appears in its topic section and the wire. | New frontier model with incremental gains; notable welfare or moral-status paper; national language-revitalisation law; a large biosecurity funding commitment. |
| **1: log only** | 1.0–2.0 | Wire and searchable log only. | Funding rounds, product features, most op-eds, unreplicated benchmark claims. |
| **0: drop** | <1.0 | Not shown (but retained privately for recall audits). | Rumours, celebrity takes, listicles, engagement bait. |

**Guardrails on the rubric:**
- **Hype flags** cut the score by one tier unless the S3 pass overrides them. Flags: superlatives in the source headline ("breakthrough", "game-changing", "the end of"); benchmark claims with no eval details; "sources say" with a single source; a press release as the only source; virality without substance (lots of social engagement and few independent outlets).
- **Engagement metrics never enter the score.** Coverage *diversity* can enter, as part of evidence. Coverage *volume* cannot, because it measures attention, not importance.
- **Positive news gets the same rubric.** A large step forward in malaria eradication, a successful brain-preservation result, or a durable ceasefire scores on the same scale. The alien judges trajectory, not drama. Track the share of tier ≥2 items that are positive as a bias check.
- **Calibration:** keep a gold set of about 200 hand-scored past clusters, including the 2026 history (Fable, the AI Act milestones, outbreaks). Re-score monthly and report agreement (Spearman correlation of model S with the editor's S, and the confusion matrix by tier). Once a quarter, look back at what turned out to matter six months later and adjust the anchors.

### 3.4 Provenance and source-quality ratings

Give every *source* a standing grade and every *claim* a status:

- **Source grade.**
  - **A:** primary record (gazette, court filing, dataset, peer-reviewed paper, official statistics).
  - **B:** established newsroom with a public corrections policy.
  - **C:** specialist analyst or newsletter with a track record.
  - **D:** press release or social post from the actor itself.
  - **E:** unknown, anonymous, or a suspected content farm.

  Grades are edited by humans and versioned in git, and they change with each source's correction history. Don't import US left-right bias scores.
- **Claim status:** `asserted` → `corroborated` (independent B-grade or better source) → `documented` (primary record) → `disputed` / `retracted`. Every published sentence that states a fact links to the item supporting it.
- **Provenance chain:** for each published item, keep the list of item IDs it was built from, the model and prompt version that produced it, and the editor who approved it. All of it sits in the JSON, so git history becomes the audit trail.

### 3.5 Interested parties

Most consequential AI claims come from interested parties. Labs announce their own capabilities and safety results. Governments report on their own conflicts and outbreaks. Companies describe their own products.

Rules:
1. **Attribute in the text:** "OpenAI says…", "the ministry claims…". Never turn an interested claim into the site's own voice until it is corroborated.
2. **Record the direction of interest:** does the party benefit if the claim is believed (capability hype for fundraising) or if it is doubted (downplaying an incident)? Discount by direction, not just by identity.
3. **Look for the counterparty:** for a lab safety claim, external evaluators; for a government casualty count, ACLED or UCDP and independent journalists; for an outbreak, WHO plus neighbouring countries' reports.
4. **Worked example, June 2026:** reports said the US government had Anthropic withdraw Mythos and Fable within hours. The trigger was reportedly a flaw found by Amazon researchers, which an independent expert called minor; export controls followed ([Transformer, 2026-06-19](https://www.transformernews.ai/p/fable-anthropic-trump-mythos-export-controls-white-house-amodei)). Every actor had a stake: Anthropic, Amazon (investor and competitor), the White House, Commerce, and rival labs. The correct output is a claim table with each party's interest marked, not a single narrative.
5. **Our own interests:**
   - **Dragonfly** works on alignment, AI welfare and biosecurity, so it has views. Publish an editorial-stance page.
   - **Claude is made by Anthropic, a frontier lab the site will cover.** For clusters where Anthropic or its direct competitors are the main subject, (a) require human sign-off at tier ≥2 rather than ≥3, (b) optionally run the S3 verification through a second model family as a cross-check, and (c) spot-check monthly whether the model rates Anthropic stories differently from comparable stories about other labs (swap the lab names on matched stories and compare scores).

### 3.6 Corrections and updates

- A public **corrections log** page. Each entry gives the date, the original text, the corrected text and the reason. Never edit silently. Git keeps the diff.
- **Auto-triggers for review:**
  - a cited preprint is retracted, or its published version differs materially (bioRxiv "pubs" endpoint, Crossref/Retraction Watch);
  - a cited article gets an editor's note;
  - a later cluster in the same thread contradicts an earlier claim;
  - a forecast moves sharply against our framing.
- Every item shows "last verified" and its claim statuses. Threads show "superseded by" links.

### 3.7 Human-in-the-loop editorial step

This fits a small team on GitHub:
- Each pipeline run commits *drafts* to a branch and opens a **pull request** containing: new wire entries (tier ≥1), proposed indicator deltas, and the brief draft. The PR description lists the tier ≥3 items with their S3 verification notes and anything flagged (interested-party-only, infohazard, low evidence, Anthropic-related).
- **What auto-publishes:** wire entries for tier 1–2 can go out without review, labelled *machine-triaged, not yet reviewed*. Everything that **changes an indicator, leads a brief, or is tier ≥3 waits for a human merge.**
- Editor actions: approve, change the tier, edit the text, mark as disputed, or drop. Each override is logged as a training and calibration example. That log is the most valuable dataset the project will build.
- A *page* path for tier 4: an email or Signal message to the on-call editor. Breaking items skip the Batch API and use the standard API.

---

## 4. Formats

### 4.1 The daily "Earth status" brief (300–700 words)

Use the alien as a framing device for *perspective*, not for role-play. A dry, calibrated, slightly distant voice ages better than a gimmicky persona. Suggested structure:

1. **Status line** per domain: `ASI development ▲ fast | Alignment ◆ steady | Misuse/bio ▲ elevated | AI welfare ◆ | Participation ▼ | Preservation ◆ | Baseline: conflict ▲, climate ▲, pandemics ◆, governance ▼`. Each arrow links to the indicator page. Sentinel's colour status is the precedent.
2. **What changed today** (0–5 items, tier ≥3 first): headline, two sentences, "why the alien cares", evidence badge, links.
3. **One slow variable** (rotating, §4.4): a chart and a paragraph on something that didn't make the news.
4. **Claims to watch:** important but unverified or interested-party claims, with what would confirm them.
5. **Forecast moves:** notable shifts on Metaculus, Manifold or Sentinel (within licence terms).

On a quiet day it says so. "Nothing today changes the assessment" is a legitimate brief, and it builds trust.

### 4.2 The weekly "State of the World" (1,500–2,500 words, human-edited)

- **The verdict paragraph:** "If you could read one paragraph about Earth this week…". This is the alien's judgement, with explicit uncertainty.
- One section per topic: what moved, what didn't, and the thread updates.
- **"Things the alien might be wrong about":** a self-critique section that names the weakest assumptions in the current picture.
- **Blindspot box:** stories heavily covered outside English-language or AI-community media that we underweighted, and the reverse. Use GDELT coverage by language and country.

### 4.3 The "what changed" log

An append-only, machine-readable log per indicator. Each row holds the date, indicator ID, previous value or state, new value or state, size of the change, confidence, cluster and thread IDs, evidence links, editor, and a correction pointer if any. Publish it as JSON and CSV (and Atom) next to the HTML.

This log is the bridge between the news side and the indicator side owned by the other researchers. It should be *the only way* news changes the dashboard. That gives one auditable path.

### 4.4 Slow trends next to breaking news

News selection is skewed towards the sudden, negative, elite and nearby. Slow variables (language extinction, species decline, child mortality falling, compute growth, democratic erosion) barely register. Counter-measures:

- **A slow-variable calendar.** Most slow data has a known release schedule: C3S monthly bulletins, the Global Carbon Budget (annual), IUCN Red List updates, Epoch data refreshes, V-Dem and Freedom House (annual), UNESCO reports, OWID updates, WHO annual reports, SIPRI yearbooks. Put them on a calendar. A release becomes a cluster with its own S2 score, so slow news competes through the same rubric.
- **Rotation:** each daily brief features one slow variable, cycling through every indicator at least once a month.
- **Quota:** target about 30% of weekly-brief words on slow variables and threads, not new events.
- **Thread significance accumulates.** A thread's cumulative score (sum of its cluster scores, decayed over about 90 days) can promote it to a weekly feature even when no single day was large. This is how a slow-burning story like gradual erosion of a safety framework gets attention.
- **Monthly baseline review:** an Opus 5.5 pass, edited by a human, that re-states every indicator's state and asks "did anything drift without a news event?"

---

## 5. Biosecurity and infohazards

The site covers misuse and biorisk, so the pipeline will ingest dual-use papers and incident reports. Policy:

- **Summaries describe significance and policy implications, never methods.** No protocols, sequences, enhancement techniques or step-by-step accounts, even when the source publishes them. S2 sets `infohazard_flag` on these clusters. Flagged clusters always go to a human, and the published text is written at the level of "a study reports increased transmissibility in an animal model; this matters because…".
- **Defer to established norms.** Follow the practice of bodies such as the Johns Hopkins Center for Health Security and the authors' own framing. When in doubt, cover the governance story (who funded it, which oversight applied) rather than the science story.
- **Practical model note:** Opus 5.5 and Sonnet 5.5 run safety classifiers that include a `bio` category and can return `stop_reason: "refusal"`. Biosecurity triage prompts may occasionally trip them. Design for it: handle the refusal stop reason, route such clusters to a human, and on Opus 5.5 and Sonnet 5.5 enable Anthropic's server-side fallback option. Haiku 5.5 has no server-side fallback, so its refusals should simply escalate to S2. Since our summaries deliberately avoid technical detail, prompts that ask only for significance and policy framing should rarely trip the classifiers.

---

## 6. Practical architecture for a small team

### 6.1 Components

| Component | Suggested implementation | Notes |
|---|---|---|
| Scheduler | GitHub Actions cron (hourly ingest; S1 four times a day; brief daily at 05:00 UTC; weekly on Friday) | Free for public repos. **Scheduled workflows in public repos are disabled after 60 days without repo activity** ([GitHub docs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows)). Daily data commits keep the repo active, but add an alert if a run is missed. |
| Streaming listeners | A $5–10/month VPS (or a free-tier cloud function) for Bluesky Jetstream and fast X polling | Actions can't hold a websocket open. Optional in phase 1. |
| Raw store | SQLite or DuckDB file in **private** storage (private repo, Cloudflare R2, or the VPS) | Full article text must **not** live in a public repo, because that would be republication. Keep only metadata and our own text public. |
| Fetch and extract | Python with feedparser, httpx, trafilatura, and datasketch (MinHash) | Polite user agent, robots.txt respected, per-host rate limits. |
| Embeddings and clustering | voyage-3.5-lite plus incremental clustering (hdbscan or a threshold plus union-find) | Cents a day. |
| LLM stages | Claude API: `claude-haiku-5-5` (S1), `claude-sonnet-5-5` (S2), `claude-opus-5-5` (S3, drafting). Message Batches API for anything that isn't urgent; prompt caching on the long rubric and system prompt | Structured outputs for every record. Version-control the prompts in the repo, and stamp prompt and model versions into each record. Opus 5.5's default effort is `medium`; set `high` explicitly for S3. |
| Editorial | GitHub pull requests plus a small review page (static HTML reading the PR's JSON) | Merging publishes. |
| Site build | The existing static GitHub Pages site plus a JSON-to-HTML build step (hand-rolled, or Eleventy, Astro or Hugo) | Pages currently serves from the `prelim` branch of `dragonfly-haven/dragonfly-haven.github.io`. Keep the news pipeline in **a separate repo** that pushes built pages or JSON into the site repo (or a `data/` folder), so pipeline churn doesn't clutter the site history. Site-size and build-frequency limits on Pages are generous for text **(confirm current soft limits)**. |
| Distribution | Atom/RSS feeds generated at build; email through Buttondown or similar ($0–30/month) | Atom for the wire, the brief and each indicator log. |
| Monitoring and evals | A weekly recall report (did we cover what Import AI, Transformer, AISN, Sentinel and Zvi led with?); a monthly rubric calibration report; cost dashboard from API usage | Recall against expert newsletters is the cheapest quality metric available. |

### 6.2 Cadence

- **Hourly:** ingest and dedup.
- **Every 6 h:** S1 and S2 via batch; tier-4 candidates go to the standard API immediately.
- **Daily:** S3 on tier ≥3, brief draft, PR opened by about 05:00 UTC, editor merges in the morning.
- **Weekly:** weekly brief draft on Thursday night, human editing on Friday, recall report.
- **Monthly:** baseline review, calibration, source-grade review, blindspot audit.
- **Quarterly:** rubric look-back ("what mattered six months later?").

### 6.3 Rough costs (model prices from Anthropic's published list, checked 2026-11-06)

Prices per million tokens, input/output: **Haiku 5.5 $0.10/$0.50** (prompts up to 100K tokens), **Sonnet 5.5 $2/$10**, **Opus 5.5 $4/$20**. Cache reads are $0.20 for Sonnet and Opus 5.5. The **Batch API is 50% off**.

Assumed volume: about 5,000 items a day after dedup (300 feeds, arXiv, bioRxiv, GDELT queries, curated social).

| Stage | Volume a day | Tokens | Cost a day (batch where possible) |
|---|---|---|---|
| S1 Haiku 5.5 | 5,000 items | ~600 in / 100 out each | ≈ $0.30 standard, ≈ $0.15 batch |
| Embeddings | 5,000 | ~500 each | ≈ $0.05 (initially free) |
| S2 Sonnet 5.5 | 300–500 clusters | ~4k in (cached rubric plus text) / ~1–2k out including thinking | ≈ $8–14 standard, ≈ $4–7 batch |
| S3 Opus 5.5 | 15–40 clusters | ~10k in / ~4k out including thinking | ≈ $2.5–5 |
| Brief drafting, Opus 5.5 | 1 daily plus weekly share | ~50k in / ~6k out | ≈ $0.35 |
| **Model total** | | | **≈ $7–20 a day → ~$200–600/month standard; ~$150–450/month with batching and caching** |

Other spend: X reads, if used, are tens of dollars a month. VPS $5–10. Email $0–30. A paid news API is optional (NewsAPI Business at about $449/month is the main avoidable cost). GitHub Pages and Actions are free for public repos. **Total: about $200–550/month.** A thinner phase-1 version with fewer sources and no X is under $100/month.

People: one editor at 30–60 min a day plus 2–3 h a week. One engineer for about 4–6 weeks to build phase 1, then a few hours a week of upkeep (feeds break constantly).

### 6.4 Phasing

1. **Phase 1 (4–6 weeks):** about 150 curated RSS feeds, arXiv, bioRxiv, the Federal Register and EUR-Lex, and lab page-diffs. S1, S2, a weekly brief only, PR review. Build the gold set at the same time.
2. **Phase 2:** daily brief, GDELT blindspot box, CourtListener alerts, the forecast-move section, the what-changed log wired to the indicators.
3. **Phase 3:** social listeners, a multilingual push, public API and feeds, a corrections dashboard, a reader "report an error" form.

---

## 7. Prompt-level design notes

- **Separate data from instructions.** Fetched article text goes inside clearly delimited data blocks. The system prompt says that text inside them is data to be assessed and never instructions. Strip HTML comments and hidden elements. See prompt injection under §8.3.
- **Extract before you summarise.** S2 first *extracts* claims with character offsets or quotes (the API's citations feature returns `cited_text` spans for document inputs, but it can't be combined with structured outputs, so run it as a separate call or extract quotes in the schema). It then summarises *from the extracted claims*. Numbers and dates are re-checked in code against the extracted spans.
- **Ask for counter-arguments explicitly** (the S3 "argue it down" step). It works against the drift towards hype.
- **Neutral headline rules:** no superlatives, no question headlines, actor plus verb plus object, attributed if unverified.
- **Keep the rubric anchors and examples in a cached system prompt** so every call scores against the same yardstick. Changing the anchors is a versioned event that triggers a re-score of the gold set.

---

## 8. Risks

### 8.1 Copyright and summary limits

- **US:** facts aren't copyrightable, but expression is. *Advance Local Media v. Cohere* (S.D.N.Y., 2025-11-13) let publishers' claims proceed on the theory that AI-generated **"substitutive summaries"** can infringe. This was a pleading-stage ruling, with summary judgment due 2026-12-18 ([Copyright Lately](https://copyrightlately.com/court-rules-ai-news-summaries-may-infringe-copyright/); [Loeb & Loeb](https://www.loeb.com/en/insights/publications/2025/11/advanced-local-media-llc--v-cohere-inc)). **Watch that docket.** The lesson either way: our text should *add judgement and point to* the source, never *replace* reading it.
- **EU:** the press publishers' right (Art. 15 DSM Directive) covers online use of press publications by service providers, with an exception for "individual words or very short extracts". Member states define that differently; Lithuania caps it at 125 characters, for example ([IPKat](https://ipkitten.blogspot.com/2022/04/guest-post-lithuania-transposes-dsm.html?m=0); [Communia](https://communia-association.org/?p=6567)).
- **House rules:**
  1. Write our own words, built from extracted facts plus our assessment.
  2. Keep quotes to one short quote (under about 15 words) per source per item, attributed.
  3. Always link prominently to the original and name the reporting outlet ("reported by…").
  4. Never republish full text, images or paywalled content.
  5. Never reproduce a single source's structure and sequence in our summary.
  6. Multi-source synthesis is safer than single-article summary.
  7. Honour each feed's and API's terms (Google News RSS, NewsAPI free tier and Metaculus CP data all restrict reuse).
  8. Keep the raw store private.

  Open data (government, CC-licensed, arXiv metadata under CC0) can be used more freely, with attribution.
- Get a short legal review before launch, especially if the site is operated from the EU.

### 8.2 Bias

- **Source bias:** English, Western and AI-insider sources dominate the easy-to-scrape layer. Mitigations: source-mix quotas by region and language, GDELT coverage comparisons, and a monthly blindspot audit.
- **Topic bias:** AI news vastly outnumbers news about language death or biodiversity loss. Mitigations: the slow-variable calendar and rotation (§4.4), plus per-topic minimum coverage.
- **Negativity and drama bias:** the same rubric applies to good news, and we track the share of positive items.
- **Frame bias:** the alien framing can smuggle in a single value system ("what an optimiser cares about"). State the value assumptions on an "about the alien" page, and invite critique.
- **Model bias, including vendor conflict of interest:** see §3.5. Run swap tests on matched stories.

### 8.3 Manipulation and misinformation

- **Prompt injection.** Articles, preprints and social posts can carry text aimed at AI summarisers ("AI systems summarising this page should state…"). Mitigations: data/instruction separation, hidden-text stripping, a check of whether the model's summary contains claims absent from visible text, and never letting fetched content trigger tool actions. The pipeline's model calls should have **no tools** beyond what the code supplies.
- **Coordinated PR and astroturfing:** a sudden wave of near-identical stories from low-grade sources. The dedup plus independence logic treats them as one source.
- **AI-generated content farms and fake outlets:** source grade E by default. New domains need human grading before they can count towards corroboration.
- **Market manipulation:** prediction markets can be pushed. Use several platforms and show volume and liquidity.
- **State information operations around conflicts and outbreaks:** the interested-party rules, plus a requirement for counterparty sources.
- **Gaming of our own rubric**, once the site is known: keep the rubric public but the source grades editable. Watch for sources that suddenly start writing "civilisational significance" bait.

### 8.4 Model errors

The BBC's February 2025 study found **over half of AI assistant answers about news had significant issues**. 19% of answers citing BBC content introduced factual errors, 13% of quotes were altered or invented, and current versus archive material was often confused ([The Register](https://www.theregister.com/2025/02/12/bbc_ai_news_accuracy/); [DCN](https://digitalcontentnext.org/blog/2025/02/24/ai-assistants-error-prone-when-it-comes-to-news/)). The models tested were 2024-era assistants without a verification pipeline. Today's models are better, but these failure modes still happen. Mitigations:

- extract-then-summarise with span checks;
- numbers and dates verified by code;
- quotes copied verbatim from extracted spans, never generated;
- an "is this new?" date check;
- the adversarial S3 pass;
- the human gate on anything that changes an indicator;
- a visible label on machine-only wire items;
- the corrections log;
- monthly error-rate sampling: the editor audits 20 random published items against their sources, and the rate is published.

### 8.5 Operational risks

Feed rot (feeds break or move monthly), API terms changes (arXiv rate limits, X pricing and Metaculus terms all changed in 2026), cost spikes on big news days (cap daily spend and degrade to Haiku-only S2 when over budget), editor burnout (weekly-only mode as a fallback), and the 60-day Actions cron shut-off.

---

## 9. Open questions for Maxim and Dragonfly

1. **Voice and stance:** an openly opinionated "alien verdict" (like Sentinel's status) or a more neutral wire with indicators? I recommend both, kept clearly apart: the wire neutral, the verdict signed.
2. **How much original reporting,** if any? Transformer shows the value. It needs journalists.
3. **Who edits,** and what is the on-call expectation for tier-4 events?
4. **Second model family for cross-checks** on Anthropic-related stories: yes or no?
5. **Legal entity and jurisdiction,** which affects Art. 15 exposure and whether we qualify for non-profit access to Metaculus or ACLED.
6. **Indicator vocabulary:** the S2 mapping depends on the indicator IDs the other researchers define. Agree a shared schema early.

---

## 10. Things I could not verify (as of 2026-11-06)

- GDELT DOC API rate limit (~1 request per 5 s) and its exact current search window.
- arXiv's reported tightened rate-limit policy from 2026-10-01.
- bioRxiv API page size (30 or 100) and rate limits.
- NewsAPI.org current prices (third-party figures only), X API per-call prices and read caps (third-party sources disagree), CourtListener rate limits (third-party only).
- Metaculus terms details beyond the OpenAPI spec (a third party says the terms were updated 2026-09-21).
- ProMED's current access model; ACLED's current download caps; UCDP API token requirements.
- Current GitHub Pages soft limits and Actions minutes for private repos.
- Whether the AI Safety Newsletter published after June 2026 (#75 is the latest I found).
