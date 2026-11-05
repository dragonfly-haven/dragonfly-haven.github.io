# 04 · The Ecosystem: who is working to make the AI transition go well, how they are funded, and how to show it

*Research note for the Dragonfly "AI and everything" civilisational dashboard. Compiled 2026-11-06. Every figure carries a date or a source, because almost everything here goes stale within months. "Unverified" means I found it in one secondary source only, or I am recalling it from background knowledge and could not check it in this session.*

Scope: this file maps the **ecosystem**: the organisations, research agendas, funding flows and communities working on alignment, governance, misuse defence, AI welfare, preservation and broad human participation. It does not cover the frontier labs, governments and chipmakers as power centres (see the key-decision-makers file), per-topic indicators (dashboard-indicators file), timelines (progress/pacing file) or the ingestion machinery (`05-news-pipeline.md`). Lab safety teams and government safety institutes come in only as parts of the ecosystem.

---

## 0. The view from orbit (summary for the alien judge)

1. **The ecosystem is tiny next to what it steers.** In 2026 the four big hyperscalers alone will spend about **$725B–$828B** on capex: about $725B in the May tally, rising to $803–828B in the Q3 tally once SpaceX is added ([HL, 2026](https://www.hl.co.uk/news/ai-hyperscalers-are-expected-to-finish-the-year-spending-a-whopping-828-billion-on-capex); [Yahoo Finance, 2026](https://finance.yahoo.com/sectors/technology/articles/hyperscalers-hit-700-billion-2026-111243744.html)). Philanthropic money for AI safety and adjacent work is expected to reach about **$1.5–2B in 2026**, up from roughly **$0.6B in 2025** (my sum of the [Manifund AI Safety Funder Bulletin](https://manifund.org/ais-funder-bulletin), updated 2026-11-01). That ratio is about **1 : 400 in 2026** and about **1 : 700 in 2025**. Government safety institutes add only hundreds of millions on top.
2. **The field is about 1,100–1,800 full-time people.** In September 2025 Stephen McAleese estimated ~600 technical and ~500 non-technical FTEs, up from ~400 in 2022, with technical FTEs growing ~21%/yr ([LessWrong, 2025-09-27](https://www.lesswrong.com/posts/8QjAnWyuE9fktPRgS/ai-safety-field-growth-analysis-2025)). A broader count based on paper authorship gives ~1,783 for 2025 ([1000 Years of AI Safety](https://1000yearsofaisafety.com/n/safety2025/)).
3. **2026 is a phase change in funding.** In a single year:
   - Coefficient Giving (formerly Open Philanthropy) went from $351M on AI in 2025 to "on track" for over $1B in AI-related grantmaking.
   - The OpenAI Foundation started granting.
   - Anthropic's cofounders and staff pledged equity, and the company set aside a further 5% of its shares in a new Public Benefit Fund (2026-10-18).
   - At least six new pooled funds launched.

   The binding constraint is shifting from money to **talent, absorptive capacity and independence**.
4. **One funder still dominates.** Coefficient Giving says it holds a "concentrated share of AI safety philanthropic funding" ([Transformer, 2026-03-12](https://transformernews.ai/p/anthropic-employees-philanthropy-billions-donations-effective-altruism-coefficient-giving-ai-safety)). A wiki estimate (no longer maintained) says ~85% of external funding comes from five sources ([Longterm Wiki](https://www.longtermwiki.com/wiki/E458)). Much of the new money also traces back to two labs, Anthropic and OpenAI, which is a structural conflict of interest for an ecosystem that is meant to check them.
5. **The most neglected areas relative to their importance** are:
   - AI welfare and digital minds: the MIT AI Risk Initiative found AI welfare had the least governance coverage of 24 risk subdomains ([Digital Minds 2025 review](https://www.lesswrong.com/posts/KGtLswHGhsdJtyi8K/digital-minds-in-2025-a-year-in-review)).
   - Model-weight and lab security.
   - Defences against power concentration.
   - Knowledge, language and brain preservation.
   - Anything outside the US/UK axis, especially the Global South, and China beyond a few bridges.

   Alignment research and evaluations are the best funded, and governance is the fastest-growing.

---

## 1. How the ecosystem fits together

```
                    ┌──────────────── WEALTH SOURCES ─────────────────┐
                    │ Moskovitz/Tuna (Good Ventures) · Tallinn · McCaleb│
                    │ Buterin (FLI) · Schmidt · Anthropic equity       │
                    │ (cofounders, staff, Public Benefit Fund) ·       │
                    │ OpenAI Foundation (~26% of OpenAI, unverified)   │
                    │ · governments (UK, EU, US, others) · labs (direct)│
                    └───────────────┬─────────────────────────────────┘
                                    │
          ┌─────────────── GRANTMAKERS / INTERMEDIARIES ───────────────┐
          │ Coefficient Giving · SFF · Lightcone Commons · Longview ·    │
          │ Macroscopic · Astralis · Navigation Fund · TAIF (ex-LTFF) ·  │
          │ Manifund · AISTOF · ARM Fund · BlueDot grants · Schmidt Sci. │
          │ · FLI · GTR Fund · UK AISI grants · ARIA · NSF · FMF AISF   │
          └───────┬─────────────┬───────────────┬─────────────┬─────────┘
                  │             │               │             │
        RESEARCH ORGS     GOVERNANCE &     FIELD-BUILDING   MEDIA &
        (alignment,       ADVOCACY         (MATS, BlueDot,  COMMUNITIES
        evals, bio,       (think tanks,    SPAR, ERA, 80k,  (Transformer,
        welfare...)       PACs, AISIs)     Constellation)   LW/AF/EAF...)
                  │             │               │             │
                  └──────► PEOPLE flow both ways with labs ◄──┘
                         (alumni → lab safety teams; lab staff →
                          nonprofits; lab money → nonprofits)
```

Five kinds of link matter, and each could become a layer in the network view:

- **Money:** grants, contracts, donations, PAC spending.
- **People:** alumni pipelines, founders spinning out of labs, shared boards.
- **Access:** pre-deployment model access for evaluators, secondments to AISIs.
- **Ideas:** research agendas cited across organisations.
- **Policy hooks:** evaluations feeding labs' safety frameworks, AISI testing agreements, the EU AI Act Code of Practice.

The densest cluster is the Berkeley/SF–London–Oxford–Cambridge (MA) triangle. Most organisations below sit in one of those four places.

---

## 2. Funding flows

### 2.1 Philanthropic funders (AI safety and adjacent work)

Unless marked otherwise, the figures are from the [Manifund AI Safety Funder Bulletin](https://manifund.org/ais-funder-bulletin), last updated **2026-11-01**. It is the best live aggregate I found. Some entries are its own estimates.

| Funder | 2024 | 2025 | 2026 (expected) | Notes |
|---|---|---|---|---|
| **Coefficient Giving** (ex-Open Philanthropy; renamed Nov 2025) | $168M on technical safety, security and fieldbuilding | $351M (self-reported); $409M in public grant lists | >$1B AI-related (reported); $1B "across catastrophic risks" (bulletin) | Funded mainly by Good Ventures (Moskovitz/Tuna). Its largest technical grant is $160M to **Resolution** (ex-Sequent), announced 2026-07-09: $108M base plus $52M conditional ([LessWrong](https://www.lesswrong.com/posts/HDKQNqiR2gtfMiWsn/announcing-our-usd160m-grant-from-coefficient-giving)). It ran a $40M technical-safety RFP in 2025 ([EA Forum](https://forum.effectivealtruism.org/posts/XtgDaunRKtCPzyCWg/open-philanthropy-technical-ai-safety-rfp-usd40m-available)), runs "Project Tailwind" ($200k–$200M) ([aisafety.com/funding](https://www.aisafety.com/funding)), and expects >$100M for biosecurity in 2026 ([AIxBio sources](https://gcbrupdates.substack.com/p/gcbr-organization-updates-september)). |
| **OpenAI Foundation** | — | $0 to safety ($40.5M unrestricted to 200+ community nonprofits, Dec 2025) | ~$250M (estimate) | $25B long-term commitment to "health breakthroughs and AI resilience"; ≥$1B planned within a year (update of 2026-03-24). $130M first resilience tranche (bio, cyber, model safety, youth), announced ~June 2026, with no grantee list published yet ([blockchain.news](https://blockchain.news/ainews/openai-foundation-launches-130m-ai-resilience-push)). $17.2M to SecureBio Detection. Resilience is led by Wojciech Zaremba. |
| **Longview Philanthropy** | — | $60M | ~$200M (figure from a removed page) | Advises major donors; runs the Digital Sentience Consortium and an RFP on extreme power concentration ([Longview](https://www.longview.org/?p=7658)). |
| **Macroscopic Ventures** | — | $30M | up to $100M | Focus on suffering risks and AI welfare. |
| **Astralis Foundation** | — | — | ~$100M | Invite-only; ">$60M mobilised by Aug 2026" per a job posting. |
| **Survival and Flourishing Fund** (Tallinn) | $41M (bulletin) / $24.0M (genealogy) | $34.9–35M (88 grants) | ~$63.6M Main Round, plus three themed rounds | Uses the S-Process. 2026 Main Round expected total is $63.64M ([SFF](https://survivalandflourishing.fund/)). Annual totals since 2020 are in the [genealogy post](https://www.lesswrong.com/posts/k4i6AibKLT54h5Syr/a-genealogy-of-ai-safety-how-directions-are-born-and-how). |
| **Lightcone Commons** | — | — | ~$45M | Launched July 2026 by Lightcone Infrastructure: quarterly S-Process-style rounds. Tallinn pledged $10M matched, Moskovitz ~$5–10M. Round 1 closed 2026-08-23; results were due about 2026-10-23 and I could not find them ([TechTimes](https://www.techtimes.com/articles/321586/20260725/lightcone-commons-launches-new-algorithm-aims-fix-ai-safety-philanthropy.htm)). |
| **AISTOF** | — | ~$15M | ~$40M | Pooled, invite-only fund. Figures come from private communications reported by the bulletin. |
| **Schmidt Sciences** | — | $10M (27 projects) | ~$20M | 2026 RFPs: Science of Trustworthy AI ($1M–$5M+), multi-agent safety, and a $10M joint call with Google DeepMind (2026-06-11). AI2050 fellowships are separate. |
| **BlueDot Impact** (as funder) | ~$2.5k | $0 | ~$11M | Took over Coefficient's career-transition grants (~Sept 2026; one aggregator source: [Atom Grants](https://atomgrants.com/grant/career-development-and-transition-funding-coefficient-giving)). |
| **GTR AI Safety Fund** | — | — | ~$10M | €50M over 3–7 years from Jan Beckers, launched 2026-09-14. |
| **Manifund** | — | $6M (144 projects) | ~$8M | Regranting platform; Falcon Fund launched April 2026. |
| **Transformative AI Fund** (replaced LTFF, Aug 2026) | LTFF ~$5–6M/yr | $1.2M | ~$4M | |
| **Future of Life Institute** | ~$5M (2024 comment estimate) | n/a | n/a | Endowed by a 2021 Buterin donation (~$500M+; from memory, unverified). Grants up to ~$2.3M; $4M program on AI-driven power concentration ([FLI](https://futureoflife.org/grant-program/mitigate-ai-driven-power-concentration/)). |
| **Frontier Model Forum AI Safety Fund** | ~$3M | — | — | $9.2M over two rounds in total. Funded by labs. |
| **Others** | | | | Navigation Fund (McCaleb), Founders Pledge, EA Infrastructure Fund, ARM Fund, Halcyon Futures (up to $5M), Cooperative AI Foundation (up to $1M), CLR Fund (s-risk), Foresight Institute, Mercor AI Safety Fund ($5M, 2026-09-15), ISPA Inspection Prize ($5–20M), NVIDIA $250M of compute over 5 years (2026-10-13, per the bulletin; I did not verify it independently). The full list of 60 funders is at [aisafety.com/funding](https://www.aisafety.com/funding). |

**Rough totals.** Summing the bulletin's 2025 actuals gives ~$570M. Its 2026 expectations sum to ~$1.85B if Coefficient's whole $1B is counted as AI, or ~$1.4B if about half of it is. For comparison:

- McAleese's January 2025 update put 2023 at about $46M (Open Phil) + $30M (SFF) + $11M (academic and government) + small amounts from others.
- A 2024 bottom-up estimate gave ~$111M, with Open Phil at $63.6M ([LessWrong](https://www.lesswrong.com/posts/WGpFFJo2uFe5ssgEb/an-overview-of-the-ai-safety-funding-situation)).
- That post estimated lab-internal safety spending at only $19–54M/yr, a figure now clearly far too low.

So external philanthropic funding grew roughly **10–15× between 2023 and 2026**.

### 2.2 Pledged money that is not yet liquid (the coming wave)

| Source | Commitment | Date | Status |
|---|---|---|---|
| Anthropic's seven cofounders | 80% of personal equity to philanthropy. About $37.8B at a $380B valuation ([Transformer, 2026-03-12](https://transformernews.ai/p/anthropic-employees-philanthropy-billions-donations-effective-altruism-coefficient-giving-ai-safety)); Fortune put it near $80B ([2026-10-26](https://fortune.com/2026/10/26/anthropic-founders-80-billion-giving-pledge/)) | Jan 2026 pledge; restated in IPO filing | The filing calls the pledges revocable and not legally binding. They need not go to AI safety. |
| Anthropic employee equity-match programme | About half of employees take part | ongoing | Together with the item below, about 20% of Anthropic's shares are set aside for the "public good" |
| **Anthropic Public Benefit Fund** | 5% of company shares, plus more at valuation milestones | 2026-10-18 ([NBC Bay Area/AP](https://www.nbcbayarea.com/news/local/anthropic-new-public-benefit-fund/4160971/)) | Named focus: labour-market impacts. At the May 2026 Series H valuation of $965B, 5% is nominally ~$48B (my arithmetic). |
| Anthropic Economic Futures Research Fund | $200M, plus a $150M "Claude Corps" fellowship | 2026-06-10 ([WTOP/AP](https://wtop.com/national/2026/06/anthropic-pledges-200-million-to-research-ais-economic-impact-as-ceo-suggests-job-loss-solutions/)) | Research agenda published |
| OpenAI Foundation | $25B (health plus AI resilience); $250M for economic futures (2026-05-27) | Oct 2025 recapitalisation | Disbursement pace unknown |
| Anthropic IPO | Filed a confidential S-1 on 2026-06-01; listing expected "as soon as" mid/late Nov 2026 at a reported $1.5–2T | — | Not confirmed as of 2026-11-06 ([Herald](https://biz.heraldcorp.com/article/10891552)). Liquidity from an IPO is what would turn the pledges into grants. |

**Implication.** Even a small fraction of this pledged wealth reaching safety, welfare or resilience would be 10–100× the field's 2025 budget. A Nan Ransohoff estimate puts total AI-wealth philanthropy at $37–100B per year, which is disputed ([Chronicle of Philanthropy, 2026-09-01](https://www.philanthropy.com/news/coefficient-giving-boosts-pledge-to-1-billion-banking-on-an-ai-windfall/)). Whether the field can absorb money at that scale without losing its independence from the labs it scrutinises is the most important ecosystem question for 2027.

### 2.3 Government money

| Body | Size | Date and source |
|---|---|---|
| **UK AI Security Institute** | Baseline reportedly £66M a year (disputed; older figures say ~£50M); **+£120M over 4 years** in the Oct 2026 Budget; >100 technical staff; priority access to >$1.5B of public compute | Oct 2026 Budget coverage ([search summary](https://www.itpro.com/business/policy-and-legislation/autumn-budget-2026-uk-tech-industry-welcomes-strong-ai-investment-focus)); exact allocation not published |
| UK AISI **Alignment Project** | £27M+ pool; first 60 projects in 8 countries; grants £50k–£1M; 800+ applications. Co-funders include OpenAI (£5.6M) and Microsoft; Anthropic and AWS per one secondary source | Announced 2026-02-20 at the India AI Impact Summit ([ResultSense](https://www.resultsense.com/news/2026-02-20-uk-ai-safety-institute-funds-60-alignment-research-projects-with-27m)) |
| UK AISI Systemic Safety and Challenge Fund grants | Smaller programmes | [gov.uk](https://gov.uk/government/news/cutting-edge-research-on-ai-security-bolstered-with-new-challenge-fund-to-ramp-up-public-trust-and-adoption) |
| UK AI Security plan (bio and cyber) | £600M pledge including a £165M biosecurity element (one secondary source) | 2026 ([aicybr](https://aicybr.com/blog/uk-ai-security-plan-biosecurity-lab-cyber-shield-nerv-2026)), unverified |
| ARIA Safeguarded AI (UK) | ~£59M programme (from memory, unverified) | 2024– |
| **US CAISI** (NIST) | ~$15M in FY2026; White House FY2027 request $27M | [cornfordandcross](https://cornfordandcross.com/market-insights/does-the-uk-spend-ten-times-more-than-the-us-on-ai-tests/) (secondary) |
| US NSF / DARPA | NSF SLES ~$10M (2024 estimate); "AI Forge" $750k–$3M+ grants | [aisafety.com/funding](https://www.aisafety.com/funding) |
| **EU AI Office** | 125+ staff; AI safety tenders up to €9.08M | secondary sources |
| Japan AISI | ~23 staff; plans to double | secondary source |
| Others | Canada, Korea, Singapore, India, Australia institutes; China's CnAISDA (founded Feb 2025) | International Network of AISIs (10+ countries) |

Government money for AI *safety* totals a few hundred million dollars a year worldwide. That is comparable to the philanthropic total, not larger. Governments' AI *capability* and sovereign-compute budgets are 10–100× bigger: the UK's £700M sovereign AI fund alone exceeds AISI's budget several times over ([Technology Magazine](https://technologymagazine.com/news/budget-2026-uk-unveils-700m-fund-for-sovereign-ai)).

### 2.4 Lab-internal and lab-funded safety

- Frontier labs employ the largest single block of safety researchers. One estimate gives ~200 FTEs on safety research across OpenAI, Anthropic and Google DeepMind in 2025 ([1000 Years of AI Safety](https://1000yearsofaisafety.com/n/safety2025/)). That looks low to me if red-teaming, safeguards and policy staff are counted, so treat it as a floor. Lab budgets for safety compute are not public.
- Lab-funded external programmes include:
  - the Anthropic Fellows Program, which includes model welfare;
  - the OpenAI Bio Bounty (universal-jailbreak reward raised to $50k, Sept 2026);
  - OpenAI's Superalignment Fast Grants ($10M, 2023–24);
  - the Frontier Model Forum AI Safety Fund;
  - lab co-funding of the UK Alignment Project;
  - Anthropic's $20M to Public First Action, later $40M in total support, restricted to policy and education.
- Evaluators are often paid by the developer they evaluate. SecureBio's AI evaluations are one example, and this draws conflict-of-interest scrutiny ([EA Forum](https://forum.effectivealtruism.org/posts/dMfgJQ2rGX8GmzdMm/thoughts-on-taking-openai-foundation-funding)). METR refuses lab money; Epoch AI accepts it ([Transformer](https://transformernews.ai/p/anthropic-employees-philanthropy-billions-donations-effective-altruism-coefficient-giving-ai-safety)).

### 2.5 Political money (a separate flow the dashboard should show)

- **Leading the Future** (pro-acceleration; backed by Andreessen Horowitz and the Brockmans, among others) raised $125M in H2 2025 ([Axios](https://axios.com/2026/04/16/ai-influence-network-cash)).
- **Public First / Public First Action** (pro-safety) is backed by Anthropic.
- AI-aligned super PACs had spent $55.7M–$65M+ on the 2026 midterms by mid-2026 ([NOTUS](https://www.notus.org/2026-election/ai-super-pacs-leading-the-future-public-first-alex-bores)).
- Anthropic employees gave $401k to campaigns, for example for Alex Bores and Scott Wiener.
- The midterms were on 2026-11-03, three days before this note, so results should be refreshed from FEC.gov.

---

## 3. The map by area

Each table gives each organisation's role, with size where I could find it. Unless dated otherwise, sizes are approximate and from 2025–2026.

### 3.1 Alignment and technical AI safety research

**Main agendas (2026).** The [genealogy post (2026-07-10)](https://www.lesswrong.com/posts/k4i6AibKLT54h5Syr/a-genealogy-of-ai-safety-how-directions-are-born-and-how) shows directions being born and fading:

- **Rising:** interpretability (arXiv papers rose from 69 in 2021 to 657 in 2025; "money lags attention"); **AI control** (Redwood); **model organisms** of misalignment; chain-of-thought monitorability (a cross-lab paper from July 2025); evaluations shifting towards security.
- **Absorbed into mainstream ML:** RLHF and reward modelling.
- **Faded as events but still alive on arXiv:** agent foundations and value learning.
- **Lost its institutional home:** scalable oversight, when OpenAI cut Superalignment in 2024.
- **New bets:** semi-automated alignment theory (Resolution), "Scientist AI" (LawZero), mathematically quantified risk (MAISI), provable or guaranteed safety (ARIA Safeguarded AI), and automated alignment research using AI agents.

| Organisation | What it does | Size or budget | Location |
|---|---|---|---|
| Lab teams: Anthropic (Alignment Science, Interpretability, Frontier Red Team, Model Welfare), Google DeepMind (AGI Safety & Alignment), OpenAI (Safety Systems, etc.) | The largest concentration of safety researchers; work on interpretability, evals and safeguards | Not public (see 2.4) | SF, London |
| **Resolution** (ex-Sequent) | Semi-automated alignment theory plus empirics. Authors include Geoffrey Irving and the founders of Timaeus (Hoogland, Murfet, van Wingerden) | $160M from Coefficient Giving (2026-07); growing fast | not stated |
| **Redwood Research** | AI control, alignment faking | ~20–40 staff (unverified) | Berkeley |
| **FAR.AI** | Robustness and interpretability research, FAR Labs coworking space, events, grantmaking | >$30M in commitments (2025) ([FAR.AI](https://www.far.ai/blog/30m-multi-funder-support)) | Berkeley |
| **LawZero** (Yoshua Bengio) | Non-agentic "Scientist AI" | >$35M (Aug 2025, after a Gates Foundation grant) ([Wikipedia](https://en.wikipedia.org/wiki/LawZero)) | Montréal |
| **Mathematical AI Safety Institute (MAISI)** | Quantifying AI risk; Fields medallist Jacob Tsimerman as scientific director ([The Logic](https://thelogic.co/briefing/fields-winning-canadian-math-researcher-launches-ai-safety-institute/)) | Probably the "$10M initial grant to an institute led by a Fields Medal recipient" that Coefficient mentions (my inference, unverified) | US |
| **MIRI** | Shifted from agent foundations to communication and policy; published *If Anyone Builds It, Everyone Dies* (Sept 2025) | ~$10–20M/yr (unverified) | Berkeley |
| **Goodfire**, **Transluce** | Interpretability as a product (Goodfire, a startup) or as public tooling (Transluce, a nonprofit) | Goodfire raised a $50M Series A in 2025 (unverified) | SF |
| **Apollo Research** | Evaluations for scheming and deception; became a PBC (2026-01-20) | Budget ~ $15M (outside estimate) | London, plus an SF office (2026) |
| **CHAI** (Berkeley), **Mila**, **Cambridge KASL**, **Oxford**, **NYU**, **MIT** | Academic alignment groups | — | — |
| **ARIA Safeguarded AI** | Guaranteed-safe AI with formal world models (davidad) | ~£59M (unverified) | UK |
| Others | Cooperative AI Foundation (multi-agent), Simplex, Iliad, AE Studio, Palisade Research, Apart Research, EleutherAI, Conjecture, Timaeus (developmental interpretability), Gray Swan and Haize Labs (red-teaming) | — | — |

McAleese's tally of his table gives interpretability ≈ **122 FTEs across 10 organisations** and evaluations ≈ **100 FTEs across 3** (2025). The largest categories are "miscellaneous technical", LLM safety, and interpretability ([LessWrong](https://www.lesswrong.com/posts/8QjAnWyuE9fktPRgS/ai-safety-field-growth-analysis-2025)).

### 3.2 AI governance and policy

**Agendas:** frontier safety frameworks and if-then commitments; third-party auditing and assurance levels; compute governance and export controls; liability and insurance; incident reporting; international coordination (AISI network, the International AI Safety Report, US–China dialogues); EU AI Act implementation (Code of Practice; the "Digital Omnibus" amendments got provisional approval in May 2026); US state legislation (California, New York); the "middle powers" agenda; and political economy (PACs). In the genealogy data, governance money rose from $0.4M in 2018 to $18.4M in 2023, and governance became "the main storyline of 2024–2026". Google Scholar profiles tagged AI governance rose from 45 (2022) to over 300 (2025).

| Organisation | What it does | Size or budget | Location |
|---|---|---|---|
| **UK AISI**, **US CAISI**, **EU AI Office**, other national institutes | Pre-deployment testing, research, grants | See 2.3 | London, DC/Gaithersburg, Brussels |
| **International AI Safety Report** | Scientific synthesis chaired by Bengio with 100+ experts; second edition released 2026-02-03 (the US withheld support) | — | [Report](https://internationalaisafetyreport.org/publication/international-ai-safety-report-2026) |
| **GovAI** | Governance research and fellowships | ~40–45 staff; budget estimates range from ~$1–4M up (conflicting) | London/Oxford |
| **CSET** (Georgetown) | National-security AI policy; foundational research grants up to $1M | Founded with a ~$55M Open Phil grant in 2019 (from memory) | DC |
| **IAPS**, **CLTR**, **RAND** (Technology and Security Policy; Meselson Center), **CNAS**, **IFP**, **FAS** | Policy research and placements | — | DC, London |
| **Forethought** | Macrostrategy: AI-enabled coups, the intelligence explosion, digital minds; ForeCast podcast | Small | Oxford |
| **AVERI** (Miles Brundage) | Auditing standards and policy (it does not run audits); "Frontier AI Auditing" paper with 48 authors, AI Assurance Levels 1–4 | Launched 2026-01 ([Fortune](https://www.fortune.com/2026/01/15/former-openai-policy-chief-creates-nonprofit-institute-calls-for-independent-safety-audits-of-frontier-ai-models)) | US |
| **CAIS** / CAIS Action Fund | Research, the AI Safety Newsletter, advocacy | — | SF |
| **Safe AI Forum** (IDAIS), **Concordia AI**, **CnAISDA** | Bridges to China and international scientist dialogues; the 2026 Singapore Consensus ([arXiv](https://arxiv.org/pdf/2608.14611)) | — | Global, Beijing |
| Advocacy: **FLI**, **Encode**, **ARI**, **Secure AI Project**, **AI Policy Institute**, **PauseAI**, **ControlAI**, **Public First** | Public pressure, legislation, polling | Public First Action has received $40M in total from Anthropic | US, UK, global |
| Critical and civil-society voices: AI Now, Ada Lovelace Institute, Oxford Martin AIGI, Data & Society | Accountability, labour, rights | — | — |

### 3.3 Biosecurity and other misuse defences (bio, cyber, weight security)

**Agendas:**

- **AI×bio capability evaluations:** SecureBio found open-weights models about 8 months behind the frontier on bio-capabilities (Sept 2026).
- **DNA synthesis screening:** IBBIS Commec, SecureDNA, and the IFP supply-chain guidance of June 2026. A *Science* paper from Oct 2025 showed AI-designed proteins can evade screening until the software is patched.
- **Metagenomic early warning**, including wastewater surveillance.
- **Medical countermeasures** (the 100 Days Mission).
- **Mirror life:** the Mirror Biology Dialogues Fund.
- **Cyber-offence evaluations:** in UK AISI's April 2026 cyber evaluations, two models completed a 32-step network-attack scenario.
- **Model-weight security:** RAND's five levels, SL1 to SL5, against 38 attack vectors ([RAND](https://www.rand.org/pubs/research_briefs/RBA2849-1.html)), plus SL5 prototype projects ([SPAR](https://sparai.org/projects/sp26/rec7NyTst8Upfp83l)).

| Organisation | What it does | Size or budget | Location |
|---|---|---|---|
| **SecureBio** | AI bio-evaluations (pre-release testing of GPT-5.5 and 5.6, review of Anthropic's chemical and biological risk report); CASPER wastewater network (49 sites in 24 cities); Zephyr nasal swabs (~30k samples) | $17.2M from the OpenAI Foundation for Detection; multi-year Coefficient grant ([GCBR Updates, 2026-09-01](https://gcbrupdates.substack.com/p/gcbr-organization-updates-september)) | Cambridge MA |
| **SecureDNA** | Free cryptographic synthesis screening | — | Global |
| **IBBIS** | Common Mechanism (Commec) screening tool; Global DNA Synthesis Map 2026; SBRC network of ~80 experts | — | Geneva |
| **NTI \| bio** | Policy, Biosecurity Index, co-leads the Africa Health Security Index | — | DC |
| **Johns Hopkins Center for Health Security** | Policy research, ELBI fellowship | — | Baltimore |
| **Blueprint Biosecurity**, **Sentinel Bio** (funder), **Active Site**, **Brown Pandemic Center**, **CEPI**, **CLTR**, **RAND**, **Mirror Biology Dialogues Fund** | Far-UVC and PPE, funding, governance, countermeasures | — | Various |
| Venture: **Valthos** ($30M first round; backers Founders Fund, Lux, OpenAI) ([Crunchbase](https://news.crunchbase.com/venture/biosecurity-ai-seed-funding-valthos-openai/)) | AI-driven threat detection and countermeasures | — | NYC |
| Cyber and weights: **UK AISI** cyber team, **RAND Meselson Center**, **Irregular** (formerly Pattern Labs; unverified), **IST**, lab security teams | Offence evaluations, weight-security standards | — | — |

**Funding:** Coefficient Giving expects >$100M for biosecurity in 2026 (its RFP closed 2026-05-11). The OpenAI Foundation lists bio and cyber among its resilience areas. UK government money is also reported (unverified). The [GCBR Organization Updates](https://gcbrupdates.substack.com/) newsletter is a ready-made monthly feed for this cluster.

### 3.4 AI welfare, model welfare and digital minds

**Agendas:** welfare assessments of frontier models (Eleos did Claude Opus 4's in 2025); indicators of consciousness and computational-functionalism debates; low-cost precautionary interventions (Anthropic's "end conversation" ability for abusive chats); model deprecation and weight preservation (Anthropic committed in Nov 2025 to preserve the weights of publicly released models; from memory, unverified); legal personhood (Ohio, South Carolina and Washington introduced anti-personhood bills in 2025); public perception ("seemingly conscious AI" debates; Suleyman argued against building it); and the scale of future digital welfare.

| Organisation | What it does | Size or budget | Location |
|---|---|---|---|
| **Eleos AI Research** | Welfare evaluations, research, annual conference (2nd edition 2026-09-18 to 20) | Small (~10 staff, unverified) | Bay Area |
| **Anthropic model welfare** (Kyle Fish; Joe Carlsmith joined 2025) | The only lab with a dedicated programme | — | SF |
| **NYU Center for Mind, Ethics, and Policy** (Jeff Sebo) | Research and the Digital Minds Research Fund (small grants) | — | NYC |
| **Rethink Priorities** | AI Cognition Initiative, Digital Consciousness Model | — | Remote |
| **Sentience Institute**, **Sentient Futures** (formerly AI for Animals), **PRISM** (seeded by Conscium), **CIMC** (California Institute for Machine Consciousness), **Future Impact Group**, **Center on Long-Term Risk** (s-risks), **Forethought** | Research, field-building, conferences | All small | UK, US |
| Fellowships | Digital Minds Fellowship (Cambridge UK, first run Aug 2026, ~15 fellows); Pivotal's AI welfare track; Anthropic Fellows | — | — |
| Funders | **Digital Sentience Consortium** (Longview, Macroscopic, Navigation Fund; first large call, amount undisclosed); Good Ventures now open to digital-minds work; Macroscopic; Foresight (whole-brain emulation) | Amounts mostly undisclosed | — |
| Advocacy | UFAIR, SAPAN | Tiny | — |

**Neglectedness:** probably the area where the gap between importance and resources is widest. The organisations number in the dozens and probably have a few tens of FTEs between them. Most funding amounts go undisclosed ([Digital Minds 2025 review](https://www.lesswrong.com/posts/KGtLswHGhsdJtyi8K/digital-minds-in-2025-a-year-in-review); [Longterm Wiki](https://www.longtermwiki.com/wiki/E391)). Expert surveys put ≥4.5% on conscious AI existing in 2025 and ≥50% by 2050 ([digitalminds.report](https://www.lesswrong.com/posts/KGtLswHGhsdJtyi8K/digital-minds-in-2025-a-year-in-review)). Dragonfly's welfare focus sits squarely here.

### 3.5 Preservation

This is the most heterogeneous cluster. It is rarely counted as "AI safety" at all, but from orbit it is civilisational insurance: what survives if the transition goes badly, and what is not lost if it goes well.

**(a) Brain preservation and cryonics.** Figures are approximate and conflict across sources ([afterlife.ai](https://www.afterlife.ai/cryonics); [Tomorrow Bio comparison](https://www.tomorrow.bio/blog/the-ultimate-human-cryopreservation-provider-comparison); [Nectome on LessWrong](https://www.lesswrong.com/posts/3i5GMhpGbDwef9Rns/nectome-all-that-i-know)).

| Organisation | What it does | Size | Location |
|---|---|---|---|
| **Alcor** | Whole-body and neuro (brain-only) cryopreservation; neuro costs ~$80k | ~1,300–1,535 members, ~263 patients | Scottsdale AZ |
| **Cryonics Institute** | Whole-body only | ~2,000 members | Michigan |
| **Tomorrow Bio** / European Biostasis Foundation | Standby teams in Europe, storage in Switzerland | €5M seed; ~800–1,000+ members | Berlin, Rafz CH |
| **Nectome** | Aldehyde-stabilised cryopreservation (whole-brain, connectome-preserving) tied to medical aid in dying; $250k pre-sales | Small | Vancouver WA; facilities planned in Oregon |
| **Brain Preservation Foundation** (Ken Hayworth) | Prizes and independent verification of preservation quality | Tiny | US |
| **Until Labs** (formerly Cradle) | Reversible organ cryopreservation (not brain-specific) | >$100M raised, including a $58M Series A led by Founders Fund | US |
| Adjacent | Astera Institute neuroscience (Doris Tsao; $600M+ over a decade), Open Brain Institute (brain simulation), connectomics projects, Foresight whole-brain-emulation grants | — | — |

**(b) Species and genetic diversity:** Svalbard Global Seed Vault and the Crop Trust; the Frozen Ark consortium; the San Diego Frozen Zoo; the Earth BioGenome Project; Revive & Restore. **Colossal Biosciences** (de-extinction plus a biobank) was valued at $10.2B in Jan 2025 and was in talks at $20–30B in July 2026 ([TechCrunch](https://techcrunch.com/2026/07/20/colossal-biosciences-reportedly-in-talks-to-raise-new-capital-at-20b-30b-valuation/)). That one company probably outweighs all philanthropic preservation work combined. I did not obtain budgets for the others this session.

**(c) Languages, culture and knowledge:**

- **Languages:** the Endangered Languages Project, ELAR (SOAS), the NSF–NEH Documenting Endangered Languages programme, and Masakhane (community-owned data for 50 African languages, 2026). An Australian Research Council grant runs from 2026 to 2028 (~A$534k) ([ARC](https://dataportal.arc.gov.au/NCGP/API/grants/DE260100695)). US federal cuts are reported to hit, for example, the Alaska Native Language Center (single student-paper source).
- **Knowledge archives:** the **Arctic World Archive** (Svalbard; became an independent Norwegian foundation in 2025; latest deposit 2026-02-28) ([AWA](https://arcticworldarchive.org/blog/arctic-world-archive-foundation/)); the **Arch Mission Foundation** (LA; a "billion-year" archive with GitHub repositories stored in the AWA); Long Now's Rosetta Project; the Internet Archive; Software Heritage; Wikimedia; Common Crawl.
- **AI-specific preservation:** preserving model weights and transcripts, a link to AI welfare. Benign AI could also help with language and culture capture, which is a positive-sum opportunity. Bloomberg Opinion argues that without community-led efforts, AI companies risk "helping bury" dying languages ([Taipei Times reprint](https://www.taipeitimes.com/News/editorials/archives/2025/10/07/2003845035)).

Preservation funding is fragmented across heritage, science and longevity funders, and almost none of it comes from AI-transition funders. No one I found frames it as part of the AI transition, so this is a gap Dragonfly could name.

### 3.6 Broad human participation: democratic input, collective intelligence, power concentration, economic distribution

**Agendas:**

- deliberative input into model behaviour (alignment assemblies, collective constitutions, community-built evaluations);
- plural and bridging algorithms (Polis, Community Notes);
- **preventing extreme power concentration**, including AI-enabled coups, secret loyalties, checks and balances in automated institutions, and compute concentration;
- **distributing the gains**: windfall clauses, sovereign or public wealth funds, UBI evidence, labour-market monitoring.

| Organisation | What it does | Size or funding | Location |
|---|---|---|---|
| **Collective Intelligence Project (CIP)** | Global Dialogues (launched at the Paris summit, 2025; used by Meta, Cohere, Taiwan's MoDA and the UK and US institutes); Weval community evals; Community Models; 2026 multilingual agricultural-AI eval with Anthropic and Karya ([CIP review](https://blog.cip.org/p/from-global-dialogues-to-democratic)) | Small | SF/global |
| **Meaning Alignment Institute**, **AI Objectives Institute** (Talk to the City), **Plurality Institute**, Taiwan **MoDA**/vTaiwan, **Stanford Deliberative Democracy Lab** (Meta Community Forums), **Remesh**, **Prolific** | Value elicitation and deliberation tools | Small (not verified this session) | — |
| Lab experiments | Anthropic Collective Constitutional AI (2023); OpenAI Democratic Inputs ($1M, 2023) | One-offs | — |
| Power concentration: **Forethought** (AI-enabled coups, 2025), **FLI** ($4M programme; power-concentration risk index), **Longview RFP**, **GovAI**, **80,000 Hours** problem profile, antitrust groups (Open Markets, AI Now) | Research, grants | Small | — |
| Economic distribution: **Anthropic Economic Futures** ($200M fund + $150M Claude Corps, June 2026; Economic Index), **Anthropic Public Benefit Fund** (labour impacts), **OpenAI Foundation** ($250M economic futures, May 2026), **Windfall Trust** (global safety net; FLI-linked), **OpenResearch** (UBI study), **GiveDirectly**, **Epoch** (GATE model), Stanford Digital Economy Lab | Research and safety-net pilots | Suddenly large: ~$600M+ committed in 2026 | — |

Economic distribution went from neglected to well funded in 2026, almost entirely with lab money. Democratic input and power concentration remain small, and the people best placed to study power concentration are often funded by the parties concentrating it.

### 3.7 Evaluations and auditing

| Organisation | Focus | Notes |
|---|---|---|
| **METR** | Autonomy and task-horizon evaluations; the "time horizon" metric | Refuses lab payment; budget ~$5M (outside estimate) |
| **Apollo Research** | Scheming and deception | PBC since Jan 2026 |
| **UK AISI**, **US CAISI** | Government pre-deployment testing | UK AISI: >100 technical staff |
| **SecureBio** | Bio | Paid by developers |
| **Epoch AI** | Benchmarks (FrontierMath etc.), compute and capex data | 23 FTE (fundraising page); accepts lab contracts ([Epoch funding](https://epoch.ai/our-funding)) |
| **AVERI** | Auditing standards | Launched 2026-01 |
| **Transluce**, **Irregular**, **Haize Labs**, **Gray Swan**, **Palisade**, **FAR.AI**, Scale AI SEAL | Tooling, red-teaming, cyber | Mix of nonprofits and for-profits |
| Insurance and assurance | AI Underwriting Company (donor to AVERI); ISPA Inspection Prize ($5–20M) for pre-deployment security inspections | An emerging market for assurance |

Evaluations received ~$96.7M in itemised grants, mostly in 2024–25 ([genealogy](https://www.lesswrong.com/posts/k4i6AibKLT54h5Syr/a-genealogy-of-ai-safety-how-directions-are-born-and-how)). The structural issue is **who pays the evaluator**. The dashboard should colour each evaluator by funding independence.

### 3.8 Forecasting

| Organisation | What it does | Funding |
|---|---|---|
| **Metaculus** | Forecasting platform and AI questions | $5.5M platform grant; $3M (2023); $2.75M (2024) from Open Phil ([Open Phil](https://www.openphilanthropy.org/organization-name/metaculus/)) |
| **Forecasting Research Institute** | Expert/superforecaster studies (XPT) | $10M general support (Feb 2025) |
| **Epoch AI** | Trends in compute, data and algorithms; GATE model | Grants plus contracts |
| **AI Futures Project** | Scenario forecasting (AI 2027), including a security forecast | Not found |
| Samotsvety, Good Judgment, Swift Centre, Sentinel, QURI, Manifold, Polymarket/Kalshi | Forecasts and markets | — |

Forecasts are inputs to the progress and timelines file. In this map they matter as infrastructure nodes that many other organisations depend on.

### 3.9 Field-building and talent pipelines

| Programme | Size and facts | Location |
|---|---|---|
| **MATS** | Summer 2026: 120 fellows and 100 mentors (MATS 8.0, Summer 2025, had 98 scholars). An Autumn 2026 cohort runs 2026-09-28 to 12-04. 527 alumni; 80% of pre-2025 alumni work in AI safety and 10% co-founded startups ([EA Forum](https://forum.effectivealtruism.org/posts/ms5EypRcnxZYuQ8eQ/mats-autumn-2026-fellowship-apply-by-june-7th)) | Berkeley, London |
| **BlueDot Impact** | Courses on AI safety, governance, biosecurity and AGI strategy; now a grantmaker (rapid, seed and career-transition grants). Coefficient gave ~$25.6M general support (June 2025) | London / online |
| **SPAR**, **ERA Cambridge**, **LASR Labs**, **ARENA**, **Pivotal**, **CBAI** (including an AIxBio fellowship), **Kairos**, **AI Safety Camp**, **Apart Research** (hackathons) | Research fellowships and upskilling | Various |
| **Constellation** (Astra fellowship), **LISA** (London Initiative for Safe AI), **FAR Labs** | Hubs and coworking | Berkeley, London |
| **80,000 Hours** | Careers advice, job board, podcast, AI in Context videos | London |
| **Anthropic Fellows**, **Horizon Institute** (policy fellows), **Tarbell** (journalism fellows and institutional grants of $50k–$500k+), Cooperative AI PhD Fellowship | Pipelines into labs, government, media | — |

The AISafety.com directory lists **104 training programmes, 582 jobs and 262 communities** at the time of fetch (2026-11-06) ([aisafety.com/map](https://www.aisafety.com/map)). Job count is a useful live indicator of demand.

### 3.10 Media, newsletters and podcasts

| Type | Outlets |
|---|---|
| Newsletters | **Transformer** (Shakeel Hashim; primarily funded by Coefficient Giving, which it discloses), **AI Safety Newsletter** (CAIS), **Import AI** (Jack Clark, Anthropic cofounder), **Don't Worry About the Vase** (Zvi Mowshowitz), **ChinAI** (Jeffrey Ding), **Digital Minds Newsletter**, **GCBR Organization Updates**, **AIxBio Briefing**, **Understanding AI**, **Interconnects**, Astral Codex Ten |
| Podcasts | 80,000 Hours, AXRP, Dwarkesh Podcast, The Cognitive Revolution, FLI Podcast, ForeCast (Forethought), Lawfare's Scaling Laws, Hard Fork (mainstream) |
| Video | Rob Miles, Rational Animations, AI in Context (80k) |
| Trackers and indices | FLI AI Safety Index, AI Lab Watch, MIT AI Risk Repository, International AI Safety Report |
| Funders of media | Tarbell, FLI Digital Media Accelerator, Coefficient capacity-building |

AISafety.com lists 82 media channels. Many of the most-read outlets have a funding or employment link to a lab or to Coefficient, and the dashboard should disclose this as metadata rather than editorialise about it.

### 3.11 Online communities

- **LessWrong** and the **Alignment Forum**, run by Lightcone Infrastructure (Berkeley; also the Lighthaven venue and now Lightcone Commons).
- **EA Forum** (Centre for Effective Altruism).
- Discords and Slacks (AI Alignment, EleutherAI), university groups (for example Harvard AISST and MIT MAIA), PauseAI local chapters, r/ControlProblem, and X and Bluesky clusters.
- EA Global and other conferences.
- AISafety.com lists 262 communities.

These communities are where research directions are born: the genealogy post traces several agendas to forum posts. They are also cheap to measure, through posts, comments and new-account growth.

---

## 4. Neglectedness: a first heat map

Ratings are my own synthesis from the evidence above. They are meant as a starting point for the dashboard, to be replaced with quantitative inputs (section 5.3). "Funding" is approximate 2026 external funding.

| Area | Importance (from orbit) | Funding 2026 | People | Growth | Funder concentration | Independence from labs | **Neglectedness** |
|---|---|---|---|---|---|---|---|
| Technical alignment research | Very high | High (~$500M+ incl. Resolution) | ~600+ FTE outside labs | Fast | High (Coefficient) | Medium | **Low–medium**: money is no longer the bottleneck, ideas and senior talent are |
| Evaluations and auditing | High | Medium–high | ~100–200 | Fast | Medium | **Low** (developers pay many evaluators) | **Medium**, mainly on independence |
| Governance and policy | Very high | Medium–high | ~500 | Fast | High | Medium | **Medium** outside US/UK/EU |
| Biosecurity × AI | Very high | Medium (>$100M Coefficient; OpenAI Foundation) | Low hundreds | Medium | High | Medium | **Medium** |
| Cyber and weight security | High | **Low** | Tens | Slow | — | Low (mostly inside labs) | **High** |
| AI welfare / digital minds | High (potentially enormous moral weight) | **Very low** (mostly undisclosed; tens of $M at most) | Tens | Fast from a tiny base | Medium | Low (Anthropic is the main lab actor) | **Very high** |
| Power concentration | Very high | **Low** (single-digit to low tens of $M) | Tens | Slow | High | Low | **Very high** |
| Democratic input / collective intelligence | Medium–high | Low | Tens | Slow | Medium | Medium | **High** |
| Economic distribution | High | **High since mid-2026** (~$600M+ lab-linked) | Rising | Very fast | Labs | **Low** | **Low on money; high on independence** |
| Brain preservation / cryonics | Contested; medium for a minority | Very low (venture-led) | Hundreds globally | Slow | — | n/a | **High** |
| Knowledge, language and species archives | Medium–high (insurance value) | Low and fragmented (outside Colossal) | Unknown | Flat or declining (some public cuts) | — | n/a | **High**, and not framed as AI-relevant at all |
| Field-building | High | High | — | Fast | High | Medium | **Low** |
| Media and sensemaking | High | Medium | — | Medium | High (Coefficient) | Mixed | **Medium**; Dragonfly's own lane |
| Non-Western ecosystems (China, India, Global South) | Very high | Very low | — | — | — | — | **Very high** |

---

## 5. How to show the ecosystem to an alien judge

The judge wants to know whether Earth is investing in steering at anything like the rate it invests in acceleration, whether the steering effort is healthy (diverse, independent, growing, well-placed), and where the holes are. Six views, in priority order:

### 5.1 The headline ratio gauge

Show one large number: **steering vs. building**. The numerator is the external AI-safety and resilience funding total (philanthropic + government + disclosed lab-funded external programmes). The denominator is hyperscaler AI capex, or better, frontier-lab R&D spend where it is available.

- 2025: ~$0.6B : ~$410B ≈ 1 : 700.
- 2026: ~$1.5–2B : ~$725–828B ≈ 1 : 400–500.

Plot it as a log-scale time series from about 2015. A second dial shows **people**: safety FTEs against total AI researcher headcount. Use a range rather than a point, and always show the as-of date.

### 5.2 A funding Sankey

Sources (wealth owners: Moskovitz, Tallinn, Anthropic equity, OpenAI Foundation, governments, labs) → intermediaries (Coefficient, SFF, Lightcone Commons, Longview, AISTOF, UK AISI…) → areas (the 3.x clusters) → organisation types. Annual, with a year slider.

The Sankey makes two things visible at once: concentration (one fat band from Good Ventures) and the 2026 influx from labs (new bands from Anthropic and OpenAI). Add a ghosted "pledged, not liquid" band so the judge can see the coming wave.

### 5.3 A neglectedness heat map

Rows are areas; columns are importance, funding, FTEs, growth, funder HHI (concentration) and independence. Each cell is coloured by a z-score. Compute it where possible:

- funding from the grant databases;
- FTEs from McAleese's sheets and LinkedIn counts;
- growth as year-on-year change;
- funder HHI from the Sankey data;
- independence as the share of an area's funding with a lab link.

Show importance as a separate, explicitly subjective column, with Dragonfly's own rating and room for others' ratings.

### 5.4 A network map

A force-directed graph:

- **Nodes** are organisations, sized by budget or FTEs and coloured by area.
- **Edges** are grants (weighted by $), people moving between organisations (alumni and founders), and access agreements (evaluator ↔ lab, AISI ↔ lab).
- Toggle layers by edge type. Clustering by geography shows the Berkeley–London–Oxford–Cambridge triangle and how thin everything else is.
- Lab nodes are drawn as large external anchors, linked to the decision-makers section.
- The "graveyard" layer (dead organisations such as FHI, closed in April 2024, and GPI, closed in 2025) shows churn.

### 5.5 Headcount and organisation count over time

Stacked areas by sub-field (technical / non-technical; then interpretability, control, evals, governance, welfare…) from 2010 to now, using McAleese's data, extended each year. Overlay the arXiv paper counts per direction from the genealogy post to show "attention vs. money" divergence. Its example: interpretability attention is outrunning its funding.

### 5.6 A new-entrants and exits timeline

A swimlane of launches, renames, pivots and closures:

- **2026:** AVERI (Jan), Apollo becomes a PBC (Jan), Resolution's grant (Jul), Lightcone Commons (Jul), TAIF replaces LTFF (Aug), GTR Fund (Sep), the Anthropic Public Benefit Fund (Oct).
- **2025:** LawZero, PRISM and CIMC.

This tells the judge whether the ecosystem is innovating or ossifying.

**Design note for an alien observer.** Avoid insider jargon in labels: write "groups checking AI models for dangerous abilities", not "evals orgs". Every number gets a hover card with its source, date and confidence. Because Dragonfly's visual language uses sketchy dash lines, *estimated* edges could be drawn dashed and *verified* ones solid, which encodes confidence without extra legend text.

---

## 6. Existing maps and databases to reuse

| Resource | What it has | Reuse notes |
|---|---|---|
| **AISafety.com** ([map](https://www.aisafety.com/map), [funding](https://www.aisafety.com/funding)) | Field map (376 entries), 60 funders, 104 training programmes, 582 jobs, 262 communities, 82 media channels; Airtable backend; maintained by Alignment Ecosystem Development; includes a "graveyard" | The best live directory. No public API was visible, so ask AED for an Airtable export or partnership. |
| **AISafety.world** ([LessWrong intro](https://www.lesswrong.com/posts/n99LGqGyQWYNyNvXG/aisafety-world-is-a-map-of-the-ais-ecosystem)) | Older visual map of organisations, people and resources | Good layout inspiration; coverage is dated. |
| **Manifund AI Safety Funder Bulletin** ([link](https://manifund.org/ais-funder-bulletin)) | Funder-by-funder annual totals and expectations; updated 2026-11-01 | The best single source for the Sankey's top layer. Manifund's own grants are public via its site and API (API from memory). |
| **McAleese, AI Safety Field Growth Analysis 2025** ([LessWrong](https://www.lesswrong.com/posts/8QjAnWyuE9fktPRgS/ai-safety-field-growth-analysis-2025)) | Google Sheets of technical (70) and non-technical (49) organisations with founding years and FTEs; Colab notebook; data shared by MATS (Ryan Kidd) | Seed data for headcount over time. Note the internal inconsistencies (629 vs 645 FTEs). |
| **McAleese, Overview of the AI Safety Funding Situation** ([LessWrong](https://www.lesswrong.com/posts/WGpFFJo2uFe5ssgEb/an-overview-of-the-ai-safety-funding-situation)) | Historical funder totals (last updated Jan 2025) | Back-fill for 2014–2024. |
| **Genealogy of AI safety (2005–2026)** ([LessWrong, 2026-07-10](https://www.lesswrong.com/posts/k4i6AibKLT54h5Syr/a-genealogy-of-ai-safety-how-directions-are-born-and-how)) | Per-direction arXiv counts, donor annual totals, event timeline | Source for "attention vs. money". |
| **Longterm Wiki** ([site](https://www.longtermwiki.com/)) | 578 organisations, 865 people, 39 laws, ~33k sources, grant records; Atom feed | **Not actively maintained since May 2026**, so use it as a historical snapshot only. |
| **Coefficient Giving grants database**, **SFF grants list**, **EA Funds / TAIF grants**, **FLI grants** | Grant-level data | Coefficient's public lists understate its AI giving (per the bulletin). |
| **ProPublica Nonprofit Explorer / Candid** (Form 990s), **UK Charity Commission**, **360Giving**, **USAspending**, **gov.uk** grant releases | Budgets and government grants | Lagging by 1–2 years but authoritative. |
| **FEC.gov**, **OpenSecrets** | PAC flows | For section 2.5. |
| **OpenAlex / arXiv / Semantic Scholar**, **Google Scholar tags** | Publication counts per agenda and per organisation | Automatable attention metrics. |
| **Epoch AI data** | Compute, capex and model trends | The denominator for the ratio gauge. |
| **MIT AI Risk Repository / governance mapping** | Risk taxonomy and coverage gaps | Rows for the neglectedness map. |
| Area newsletters: GCBR Organization Updates (monthly), AIxBio Briefing (quarterly), Digital Minds Newsletter, AI Safety Newsletter, Transformer | Org-level news | Feed into the news pipeline (see `05-news-pipeline.md`). |
| **1000 Years of AI Safety** ([2025](https://1000yearsofaisafety.com/n/safety2025/)) | An alternative FTE methodology (paper authors) | Use as an upper-bound band. |

---

## 7. Keeping it current

1. **Cadence by volatility.**
   - Weekly: funder announcements, new organisations, PAC filings in election season.
   - Monthly: newsletter-derived organisation updates, job counts.
   - Quarterly: Sankey totals, heat-map recompute.
   - Annually: FTE census and 990-based budgets.
2. **Automated harvesting, human sign-off.** The news pipeline flags candidate events: "launches", "grant", "raises", "renamed", "closes". An LLM extracts them into a structured record (organisation, counterparty, $, date, area, source URL, confidence). A human approves each record before it changes a published number. Keep a public change log ("2026-11-06: Lightcone Commons round 1 totals added").
3. **Every number is a record with an as-of date and a confidence level**: verified primary, single secondary, or estimate. Display the confidence (solid vs dashed lines, as in 5.6). Numbers more than 12 months old fade visually.
4. **Partner rather than duplicate.** AISafety.com (AED), Manifund's bulletin and McAleese's sheets are each maintained by one or two volunteers. Dragonfly could contribute fixes upstream and pull from them, which is cheaper and more cooperative than a parallel census. The death of Longterm Wiki's maintenance in May 2026 shows how fragile solo-maintained maps are.
5. **Annual self-survey.** A short form sent to listed organisations (FTEs, budget, funders by share, lab-funding yes/no) would produce the independence column, which no existing map has.
6. **Watch-list for 2026–27 events that will move the map:**
   - Anthropic's IPO and the liquidity that follows (pledges turning into grants);
   - the OpenAI Foundation's grantee lists;
   - the Lightcone Commons round 1 results;
   - the remaining SFF 2026 themed rounds;
   - Coefficient's 2026 year-end total;
   - the second round of the UK Alignment Project;
   - the next UK AISI budget allocation;
   - US CAISI's FY2027 appropriation;
   - EU AI Office enforcement of the AI Act from Aug 2026 (from memory);
   - post-midterm FEC totals.

---

## 8. Where Dragonfly fits

- **On the map:** Dragonfly spans three clusters (alignment, AI welfare, biosecurity), and few groups combine welfare with misuse defence. It should appear as a small node with edges to each cluster, and honestly so: tiny, and new.
- **The niche this site fills:** the ecosystem has many directories (AISafety.com), several one-off analyses (McAleese, the genealogy post) and one live funding tracker (Manifund). What it lacks is a **civilisational sensemaking layer**: one that puts steering effort next to building effort, includes the "non-AI-safety" pieces (preservation, democracy, distribution, welfare) that matter from orbit, and shows independence and concentration. That is a public good, and no one else currently does it.
- **Credibility asset:** disclose Dragonfly's own funding and lab links on its own node. Most media in this space are funded by Coefficient or have lab ties, so a transparent independence column is both a feature and a differentiator.
- **Content Dragonfly is unusually placed to add:**
  - a maintained AI-welfare sub-map, since that cluster has no good directory beyond newsletter reviews;
  - the preservation cluster framed as part of the AI transition, a framing no one else uses;
  - the bio-misuse cluster linked to the AI evaluation cluster, because the two communities overlap (SecureBio, CBAI) but are mapped separately.
- **Risk to manage:** a map that rates organisations' neglectedness or independence will be read as a funding signal. Keep the ratings transparent, sourced, and open to contest. A comments or corrections channel per node would help.

---

## 9. What I could not verify (as of 2026-11-06)

- Budgets or headcounts for METR, Redwood, MIRI, Eleos, CIP, Meaning Alignment Institute, AI Objectives Institute, IAPS, CLTR, Forethought, AI Futures Project, the Internet Archive, the Crop Trust, Frozen Ark and the Earth BioGenome Project. Figures given for some of them are outside estimates or from memory and are labelled.
- Lightcone Commons round 1 results (due ~2026-10-23); OpenAI Foundation resilience grantees; Schmidt Sciences 2026 awardees; the full SFF 2026 grant list.
- The BlueDot takeover of Coefficient's career-transition grants (one aggregator source); the UK £165M biosecurity element; AWS and Anthropic co-funding of the Alignment Project.
- NVIDIA's $250M compute commitment (bulletin only; my web-search budget ran out before I could check it independently).
- Whether MAISI is Coefficient's "Fields Medal institute" grantee (my inference).
- The OpenAI Foundation's equity stake (~26%, from memory of the Oct 2025 recapitalisation).
- Lab-internal safety headcounts and budgets, which are not public anywhere.
- Coefficient's own pages on its 2026 AI scaling returned HTTP 403, so the "$351M in 2025 / >$1B in 2026" figures rest on the bulletin, Fox News via Digg, and other secondary reports.
- Several facts are flagged "from memory": Buterin's FLI endowment, the CSET founding grant, ARIA Safeguarded AI's size, Anthropic's Nov 2025 commitment to preserve model weights, Goodfire's Series A, and the Irregular/Pattern Labs rename.
