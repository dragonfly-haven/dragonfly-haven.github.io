# 02 — Key Decision Makers

*Research note for the Dragonfly "AI and everything" civilisational dashboard. Compiled 2026-11-06. Scope: the people and institutions whose choices most affect how the transition to advanced AI goes. Dashboard indicators, timelines and pacing, the wider ecosystem of organisations and funders, and the news pipeline belong to the sibling notes and are only cross-referenced here.*

**Read this first.** Roles in this field change every few months, and in 2026 several did. The UK has a new Prime Minister, Google DeepMind has a new day-to-day head, xAI was absorbed into SpaceX, and the US AI safety institute lost its director. Every row below carries an "info date". Rows tagged **[nr]** ("not re-verified") rest on prior knowledge (to mid-2026) and were not reconfirmed by a fresh source for this note. Several 2026 figures come from secondary or aggregator sites; where only weak sources exist, the text says so. Nothing here is a claim about anyone's character or motives. It covers roles, public statements and documented actions only.

---

## 1. Method: what counts as a "key decision maker" for an alien judge

### 1.1 The question being asked

Imagine an observer above Earth asking: *whose choices, in the next one to five years, change the odds that the transition to advanced AI goes well?* That is narrower than "who is influential in AI". A popular commentator with no levers ranks lower than an obscure export-control official who signs licences. A national leader whose country has no frontier compute ranks lower than the chief executive of a memory-chip maker.

### 1.2 Levers of power (the dimensions)

A decision maker holds at least one of these levers. Each row in the tables names the lever.

| Code | Lever | What it lets you do | Examples |
|---|---|---|---|
| **C** | Frontier compute | Decide who can train and run the largest models | Hyperscalers, SpaceXAI, Stargate partners |
| **T** | Training and deployment | Decide what gets built, when it ships, which safeguards apply | Lab CEOs, boards, safety committees |
| **H** | Chips and hardware chokepoints | Decide how much compute exists at all, and where it goes | Nvidia, TSMC, ASML, SK hynix, Samsung, Huawei |
| **R** | Regulation and law | Bind labs by law: disclosure, evaluation, liability, bans | EU AI Office, US Congress and states, China's CAC |
| **X** | Export control and geopolitics | Decide which countries get chips, and on what terms | US Commerce/BIS, the White House, Beijing's counter-controls |
| **K** | Capital | Fund or refuse to fund the next round of scale | SoftBank, sovereign funds, hyperscaler balance sheets, public markets after IPOs |
| **M** | Military and intelligence use | Set terms for, and demand, military deployment | US Department of War (formerly Defense), PLA |
| **B** | Biosecurity | Gate the physical step from design to pathogen | DNA synthesis firms, screening standards, BWC, WHO |
| **S** | Standards, evaluation, convening | Define "safe enough", run tests, set agendas | AI safety and security institutes, UN panel, OECD, summits |
| **V** | Voice | Shift what elites and publics believe, which then moves the other levers | Leading researchers, coalitions, political spending |

### 1.3 How to tier without false precision

A numerical "power score" would be false precision. Use **ordinal tiers**, each with a short stated reason and a confidence level:

- **Tier 0 — pivotal chokepoints.** Actors whose single decision could, within months, materially speed up, slow down or redirect frontier development worldwide. Typically fewer than 15 actors.
- **Tier 1 — major shapers.** Large effect on pace or direction, but they need others to act with them, or act only in one region or one domain.
- **Tier 2 — significant.** Real but bounded influence: one jurisdiction, one input, or a convening role without binding power.
- **Tier 3 — watch list.** Low current leverage but plausible fast rise, or key in a narrow tail-risk domain such as biosecurity.

Rules of thumb for tiering:

1. **Rank by levers, not prominence.** Ask "what can they actually stop or start?"
2. **Count veto points separately from accelerator points.** Some actors can only speed things up (capital); others can stop things (chip chokepoints, export authorities, lab boards in principle). The "who could pause this" view (section 5) depends on this split.
3. **Show uncertainty explicitly.** Give each tier assignment a confidence of high, medium or low.
4. **Separate an institution from the person in it.** The office persists while holders change, as with CAISI in 2026. The site should show both and date the person.
5. **Stated position ≠ revealed behaviour.** Record public statements on safety and pacing with a source, and record documented actions separately. Do not infer motives.

---

## 2. Tiered lists

The tables use these columns: **Lever(s)**, **What they control / why it matters**, **Stated position on safety and pacing (with source)**, and **Info date**.

### 2.1 Tier 0 — pivotal chokepoints (as of 2026-11-06)

| Actor | Lever(s) | What they control / why it matters | Stated position on safety and pacing | Info date |
|---|---|---|---|---|
| **US President (Donald Trump) and White House** | X, R, M, K | Sets export-control policy, which in January 2026 moved Nvidia H200-class chips for China to case-by-case review with a 50% volume cap and a 25% tariff ([Federal Register, 15 Jan 2026](https://www.govinfo.gov/content/pkg/FR-2026-01-15/html/2026-00789.htm)). Pushes federal preemption of state AI laws: an executive order of 11 Dec 2025 created a DOJ AI Litigation Task Force ([Paul Hastings](https://www.paulhastings.com/insights/client-alerts/president-trump-signs-executive-order-challenging-state-ai-laws)), and a legislative framework followed in March 2026 ([Gibson Dunn PDF](https://www.gibsondunn.com/wp-content/uploads/2026/03/toward-a-national-ai-policy-the-trump-administration-releases-proposed-framework-for-federal-legislation.pdf)). Held AI talks with Xi in May (Beijing) and September (Washington) 2026 ([Bloomberg](https://bloomberg.com/news/articles/2026-05-15/trump-says-he-discussed-ai-guardrails-nvidia-s-chips-with-xi); [Al Jazeera](https://www.aljazeera.com/news/2026/9/25/trump-hails-very-productive-talks-with-chinas-xi)). | Emphasises winning the race and light regulation through the AI Action Plan. Trump said he discussed "AI guardrails" with Xi in May 2026. Reports say the September summit produced an agreed AI dialogue, and possibly a communication channel, but no official joint text was found ([ARY/Reuters](https://arynews.tv/china-us-agree-to-ai-dialogue-tariff-cuts-on-goods-during-xi-visit)). | 2026-09 |
| **General Secretary Xi Jinping and the CCP leadership (Premier Li Qiang)** | R, X, M, K | Direct China's state AI strategy. The 15th Five-Year Plan (adopted 13 Mar 2026) mentions AI about 50 times, sets the "AI+" target of AI in 90% of the economy by 2030, and for the first time includes AI safety language, such as a "full life-cycle risk management system" ([SCMP](https://www.scmp.com/tech/policy/article/3345586/chinas-five-year-plan-emphasises-orderly-ai-development-amid-global-tech-volatility); [AI Safety in China](https://aisafetychina.substack.com/p/ai-safety-in-the-15th-five-year-plan)). Sponsors the World AI Cooperation Organization (WAICO), whose founding agreement 29 countries signed in Shanghai in July 2026 ([Gansu gov / Xinhua](https://ydyl.gansu.gov.cn/enggsydyl/news/topnews/202607/t20260717_38273.html)). | Officially "safe and orderly" development, together with technological self-reliance and opposition to "technological monopoly" ([Free Malaysia Today, Li Qiang 2025](https://www.freemalaysiatoday.com/category/business/2025/07/26/chinas-premier-li-proposes-global-ai-cooperation-organisation)). | 2026-07 |
| **Nvidia (CEO Jensen Huang) [CEO nr]** | H, K | Dominant AI accelerator supplier. Reportedly holds about 60% of TSMC's CoWoS advanced-packaging capacity and has booked more than half of the 2026–27 expansion ([secondary: Fusion Worldwide](https://info.fusionww.com/blog/inside-the-ai-bottleneck-cowos-hbm-and-2-3nm-capacity-constraints-through-2027)). Also a major investor across labs. Market value briefly passed $5.5T in May 2026 (secondary). | Publicly lobbies to sell into China. Has said China is a potential market of about $50B a year. Assumed zero China data-centre revenue in its FY27 Q1 guidance ([Motley Fool via Yahoo](https://finance.yahoo.com/markets/stocks/articles/jensen-huang-bold-market-cap-174700120.html)). Generally sceptical of slowdown arguments **[nr]**. | 2026-05 |
| **TSMC (Chair and CEO C.C. Wei) [nr for title]** | H | Makes nearly all leading-edge AI logic and runs the CoWoS packaging bottleneck. On the 16 Jul 2026 earnings call, Wei said packaging capacity is "so tight that now it's limiting my customers' growth" (quoted in [secondary](https://info.fusionww.com/blog/inside-the-ai-bottleneck-cowos-hbm-and-2-3nm-capacity-constraints-through-2027)). Exposed to Taiwan Strait risk. | Commercial neutrality. No public pacing position. | 2026-07 |
| **ASML (CEO Christophe Fouquet) [nr]** | H | Sole supplier of EUV lithography. Dutch and US export licensing of ASML tools sets China's ceiling for advanced chipmaking. | Commercial. Has complied with export controls. | [nr] mid-2026 |
| **OpenAI (CEO Sam Altman; Board Chair Bret Taylor; OpenAI Foundation)** | T, C, K, V | Leading frontier lab. Recapitalised in Oct 2025 as OpenAI Group PBC, controlled by the OpenAI Foundation, which holds about 26% plus a warrant; Microsoft holds about 27% ([eWeek](https://www.eweek.com/news/openai-restructure-for-profit/)). Stargate partner with SoftBank, Oracle and MGX. Filed a confidential S-1 in June 2026, with timing not yet decided ([Fortune](https://fortune.com/2026/06/09/openai-files-confidential-s-1-sec-ipo/)). Zico Kolter chairs the Safety & Security Committee, which can halt releases ([SecurityWeek](https://www.securityweek.com/who-is-zico-kolter-a-professor-leads-openai-safety-panel-with-power-to-halt-unsafe-ai-releases/)). | Public internal targets: an "AI research intern" by Sep 2026 and a fully automated AI researcher by Mar 2028. Altman: "We may totally fail at this goal" ([TechRadar](https://www.techradar.com/ai-platforms-assistants/chatgpt/openai-roadmap-revealed-ai-research-interns-by-2026-full-blown-agi-researchers-by-2028)). Runs a Preparedness Framework with bio, cyber and self-improvement thresholds. President Greg Brockman co-funds the Leading the Future super PAC network, which opposes state AI regulation ([NYT tally via AI Weekly](https://aiweekly.co/alerts/openai-anthropic-aligned-pacs-spent-557m-on-2026-midterms)). | 2026-06 |
| **Anthropic (CEO Dario Amodei; President Daniela Amodei; Long-Term Benefit Trust)** | T, C, V | Frontier lab, maker of Claude. Released Opus 5.5 on 22 Sep 2026. Filed a public S-1 on 26 Oct 2026 for a Nasdaq listing as "ANT" ([SEC EDGAR](https://www.sec.gov/Archives/edgar/data/0002130357/000162828026067168/anthropicpbc-sx1.htm); [Anthropic news](https://www.anthropic.com/news)). Under the filing, the LTBT elects a majority of the board through Class T stock, and a co-founder entity reportedly holds 50.1% of voting power ([Decrypt](https://decrypt.co/381818/anthropic-makes-ipo-filing-public-plans-nasdaq-listing-under-ant)). Reported $65B Series H at a $965B post-money valuation in May 2026 (secondary: [LDS](https://letsdatascience.com/news/anthropic-secures-65b-nears-1-trillion-valuation-c237d543)). Compute comes from Google (up to 5 GW of TPUs) and Amazon (New Carlisle). The Pentagon designated it a "supply-chain risk" in Mar 2026 after it refused to drop limits on mass surveillance and fully autonomous weapons. A federal judge ruled against the designation, but the Pentagon said in Sep 2026 that it remains in effect ([Washington Examiner](https://washingtonexaminer.com/policy/defense/4711931/pentagon-anthropic-supply-chain-risk-despite-court-ruling)). | RSP v3.0 (24 Feb 2026) separates unilateral commitments from those that need industry-wide action and adds a Frontier Safety Roadmap and risk reports every three to six months. Current version is 3.4 (8 Jul 2026) ([Anthropic RSP](https://anthropic.com/news/responsible-scaling-policy-v3)). Amodei's essay "The Adolescence of Technology" (Jan 2026) calls advanced AI a civilisational test and supports transparency laws ([Fortune](https://fortune.com/2026/01/27/anthropic-ceo-dario-amodei-essay-warning-ai-adolescence-test-humanity-risks-remedies/)). Gave $40M to Public First Action, restricted to non-electoral use (secondary). | 2026-10 |
| **Alphabet / Google DeepMind (CEO Sundar Pichai; DeepMind Chair Demis Hassabis; SVP Koray Kavukcuoglu)** | T, C, H | Frontier lab (Gemini), plus TPUs, an in-house chip line that is the main non-Nvidia frontier compute. Reorganised on 5 Aug 2026: Hassabis became DeepMind Chair and Alphabet Chief Scientist, Kavukcuoglu took over day-to-day leadership of Gemini and frontier research and reports to Pichai, and Jeff Dean left ([Business Today](https://www.businesstoday.in/technology/news/story/google-deepmind-leadership-changes-547553-2026-08-06)). Committed up to $40B to Anthropic and 5 GW of TPU capacity in Apr 2026 (secondary: [Cybernews](https://cybernews.com/ai-news/google-to-invest-up-to-40b-in-anthropic-as-ai-rivalry-accelerates/)). | Runs a Frontier Safety Framework **[nr for 2026 changes]**. Hassabis has long called for international coordination and "CERN for AGI"-style approaches **[nr]**. | 2026-08 |
| **Microsoft (CEO Satya Nadella [nr]; MAI CEO Mustafa Suleyman)** | C, K, T | Owns about 27% of OpenAI. Fairwater data centres. The renegotiated contract lets Microsoft pursue AGI independently, and it formed the MAI Superintelligence Team in Nov 2025 ([Fortune](https://fortune.com/2025/11/06/microsoft-launches-new-ai-humanist-superinteligence-team-mustafa-suleyman-openai)). | Suleyman frames the work as "humanist superintelligence" and says Microsoft would halt systems that could run out of control (secondary). | 2026-05 |
| **US Commerce Department (Secretary Howard Lutnick; BIS Under Secretary Jeffrey Kessler)** | X, S | BIS writes and enforces chip export rules. On 31 May 2026 it issued guidance requiring licences for advanced chips going to subsidiaries of Chinese parents anywhere in the world ([The Star/Reuters](https://www.thestar.com.my/business/business-news/2026/06/01/us-takes-step-to-halt-nvidia-ai-chip-shipments-to-chinese-firms-outside-china)). Kessler confirmed in July 2026 testimony that H200 shipments to China had started ([Rep. Young Kim](https://youngkim.house.gov/2026/07/14/rep-young-kim-confronts-export-control-gaps-in-the-ai-arms-race-with-under-secretary-jeffrey-kessler/)). Commerce also houses CAISI. Approved Blackwell exports to G42 (UAE) and Humain (Saudi Arabia) in Nov 2025 ([The National](https://www.thenationalnews.com/future/technology/2025/11/20/uae-ai-nvidia-chips-us/)). | Promoting "the American AI stack". Critics, including the House Select Committee on China, argue that enforcement is weak ([IAPS](https://www.iaps.ai/research/bis-licensing-policy-for-h200s)). | 2026-07 |

Why Tier 0 is so small: building frontier compute runs through Nvidia, TSMC, ASML and a handful of memory makers. Rights to export it run through Washington, with Beijing as the only rival system. Frontier training at the very top happens at about five organisations. An alien would see that **a dozen or so decision nodes sit upstream of almost everything else**.

### 2.2 Tier 1 — frontier labs and compute owners

| Actor | Lever(s) | What they control / why it matters | Stated position on safety and pacing | Info date |
|---|---|---|---|---|
| **SpaceX / SpaceXAI (Elon Musk)** | C, T, V | SpaceX acquired xAI in Feb 2026, and xAI was folded into a SpaceX AI unit in May 2026 ([Built In](https://builtin.com/articles/elon-musk-consolidates-xai-spacex-20260203)). Colossus 2 is projected to be the largest AI data centre (about 1.1M H100-equivalents, Jul 2026) ([Epoch AI](https://epoch.ai/data-insights/largest-data-center-compute)). SpaceX listed on Nasdaq in June 2026, and filings show Musk with about 82–85% of voting power ([Wikipedia](https://en.wikipedia.org/wiki/Initial_public_offering_of_SpaceX); [Reuters via The Star](https://www.thestar.com.my/tech/tech-news/2026/04/21/exclusive-musk-and-insiders-to-retain-voting-control-of-spacex-after-ipo-filing-shows)). Plans orbital data centres; an FCC filing covers up to one million satellites. Notably, Epoch lists Colossus 1 as "used by Anthropic". | Has long said AI is an existential risk while racing to build it **[nr for 2026 statements]**. | 2026-06 |
| **Meta (CEO Mark Zuckerberg; Chief AI Officer Alexandr Wang)** | T, C | Meta Superintelligence Labs released Muse Spark on 8 Apr 2026. It is closed-weights, a shift away from open Llama ([Fortune](https://fortune.com/2026/04/08/meta-unveils-muse-spark-mark-zuckerberg-ai-push/)). Prometheus held about 760k H100-equivalents in May 2026, and Hyperion is projected at about 3.7M by 2028 ([Epoch AI](https://epoch.ai/data-insights/largest-data-center-compute)). Zuckerberg holds majority voting control **[nr]**. Did not sign the EU GPAI Code of Practice. | Moved from open weights toward closed for frontier models. Has not published a detailed pacing commitment **[nr]**. | 2026-05 |
| **Amazon / AWS (CEO Andy Jassy [nr])** | C, K | Anthropic's main training partner. New Carlisle reached about 690k H100-equivalents in Mar 2026 ([Epoch AI](https://epoch.ai/data-insights/largest-data-center-compute)). Major Anthropic shareholder. Trainium chips. | Commercial. Signed the frontier safety commitments **[nr]**. | 2026-06 |
| **Oracle [leadership nr]** | C | Stargate builder and operator, including Stargate UAE ([The National](https://www.thenationalnews.com/future/technology/2025/11/20/uae-ai-nvidia-chips-us/)). Part of the five hyperscalers that Epoch-based coverage says hold about two-thirds or more of AI compute (secondary). | Commercial. | 2025-11 |
| **DeepSeek (founder Liang Wenfeng [nr])** | T, V | China's leading open-weights frontier lab. V4 preview (24 Apr 2026): 1.6T-parameter MoE, adapted for Huawei Ascend, with part of the Flash variant trained on Ascend ([TechRepublic](https://www.techrepublic.com/article/news-apac-deepseek-v4-ai-model-huawei-ascend-chips-support/)). Open weights set the floor for global capability diffusion. | Releases weights openly. Little public safety commentary **[nr]**. | 2026-04 |
| **Alibaba / Qwen (CEO Eddie Wu [nr])** | T, C | Leading Chinese open-weights family (previews of Qwen 3.7). Capex grew 75% year on year in the quarter to Jun 2026, and the company says it will exceed its RMB 380B three-year plan ([SEC 6-K](https://www.sec.gov/Archives/edgar/data/0001577552/000110465926099220/tm2623667d1_ex99-1.htm)). Backs Moonshot. Qwen lead Lin Junyang reportedly left (secondary). | Open weights. **[nr]** | 2026-06 |
| **Huawei (Ascend)** | H | China's domestic accelerator alternative. Ascend 950 supernodes support DeepSeek V4 ([HuaweiCentral](https://www.huaweicentral.com/deepseek-launches-new-v4-ai-models-running-on-huawei-chips/amp/)). It decides how far China can scale without Nvidia. | Commercial and national self-reliance. | 2026-04 |
| **SK hynix, Samsung, Micron (HBM)** | H | High-bandwidth memory is a binding constraint. SK hynix's CEO reportedly said 2027 will be the worst memory shortage in industry history (Reuters, 10 Jul 2026, via [secondary](https://info.fusionww.com/blog/inside-the-ai-bottleneck-cowos-hbm-and-2-3nm-capacity-constraints-through-2027)). Micron said its HBM for 2025–26 is fully booked. | Commercial. | 2026-07 |
| **US Department of War (Secretary Pete Hegseth; Under Secretary for R&E Emil Michael)** | M, K | Signed deals around 30 Apr 2026 with OpenAI, Google, Nvidia, Microsoft, AWS, SpaceX and Reflection to deploy frontier AI on classified networks, with Oracle joining later ([Federal News Network](https://federalnewsnetwork.com/defense-news/2026/05/dod-strikes-deals-with-major-tech-firms-to-deploy-ai-on-classified-networks/)). Led the Anthropic supply-chain-risk designation. Its procurement terms set norms on surveillance and autonomous weapons use. | Aims for an "AI-first War Department" (Michael, quoted in the same coverage). Insists that vendors not restrict lawful military use. | 2026-09 |

Other labs to track at Tier 2 (all **[nr]**): ByteDance Seed (Doubao), probably China's largest AI capex among private firms; Moonshot AI (Kimi K3; Hong Kong IPO filed confidentially at a reported valuation of at least $50B ([Dealroom](https://dealroom.co/news/info-kyt1c4-moonshot-ai-files-confidentially-for-hong-kong-ipo/))); Zhipu and MiniMax, both listed in Hong Kong in Jan 2026 ([36Kr](https://eu.36kr.com/en/p/3740465529684233)); Tencent; Mistral AI (CEO Arthur Mensch), Europe's flagship, reportedly raising at about €20B with $830M of debt for Paris-area compute (secondary: [Startup Fortune](https://startupfortune.com/?p=13650)); Safe Superintelligence (Ilya Sutskever); Thinking Machines Lab (Mira Murati); Reflection AI, which is in the Pentagon classified-network deals.

### 2.3 Tier 1–2 — governments and their key AI officials

| Actor | Tier | Lever(s) | What they control / why it matters | Stated position | Info date |
|---|---|---|---|---|---|
| **US: OSTP Director Michael Kratsios; PCAST co-chairs Kratsios and David Sacks; Senior Policy Advisor for AI Sriram Krishnan** | 1 | R, X | Write the AI Action Plan and the federal preemption framework. Sacks left the "AI and crypto czar" special-employee post in Mar 2026 and now co-chairs PCAST ([Daily Signal](https://www.dailysignal.com/?p=132663)). | Pro-acceleration and against "patchwork" state rules. Treat "AI safety" framing as secondary to competitiveness. | 2026-03 |
| **US Congress (119th; 2026 midterm results pending)** | 1 | R, K | Could pass preemption (the Obernolte–Trahan three-year draft) or frontier rules. Stalled as of mid-2026 ([Global Policy Watch](https://www.globalpolicywatch.com/2026/07/backlash-to-bipartisan-ai-omnibus-illustrates-preemption-impasse/)). Midterms were held on 3 Nov 2026. Pre-election forecasts favoured Democratic House control ([DDHQ via Political.org](https://political.org/2026/10/27/2026-midterms-when-polls-close-on-election-night-and-when-results-are-expected/)). **Results not verified for this note.** AI super PACs spent more than $55M ([AI Weekly/NYT](https://aiweekly.co/alerts/openai-anthropic-aligned-pacs-spent-557m-on-2026-midterms)). | Divided. Bipartisan interest in child safety and chips, but split on preemption. | 2026-11 |
| **US states: California (SB 53, Frontier AI transparency, in force since 1 Jan 2026 [nr]; author Sen. Scott Wiener); New York (RAISE Act [nr])** | 2 | R | The only binding frontier-model transparency laws in the US. Targets of the DOJ AI Litigation Task Force, set up 9 Jan 2026 ([Weintraub](https://www.weintraub.com/2026/01/trumps-ai-executive-order-state-ai-laws-under-attack)). No DOJ suit against SB 53 was found. California also elected a new governor on 3 Nov 2026 (result not verified). | Pro-transparency. | 2026-01 |
| **China: Cyberspace Administration of China (CAC); MIIT; MOST; Vice Premier Ding Xuexiang (science and technology portfolio) [nr]** | 1 | R | The world's most detailed operating AI rulebook: generative AI measures, mandatory content labelling since 1 Sep 2025, anthropomorphic-AI measures effective 15 Jul 2026, and a Cybersecurity Law amendment covering AI from 1 Jan 2026 ([China Briefing](https://www.china-briefing.com/news/china-ai-regulations-2026-enforcement-guidance-compliance/)). Model filing and registration gives the state pre-deployment visibility. | "Safe and orderly". No comprehensive AI law yet ([DLA Piper](https://intelligence.dlapiper.com/artificial-intelligence?c=CN)). | 2026-09 |
| **EU: Commission (President Ursula von der Leyen; EVP for Tech Sovereignty Henna Virkkunen [nr]); AI Office (Director reported as Lucilla Sioli, single source)** | 1 | R, S | AI Act. GPAI obligations have applied since Aug 2025, and **Commission enforcement powers over GPAI began 2 Aug 2026**, with fines up to 3% of turnover ([Beam](https://beam.ai/agentic-insights/eu-ai-act-enforcement-august-2-2026-gpai-fines)). The Digital Omnibus postponed high-risk rules: Annex III to 2 Dec 2027 and Annex I to 2 Aug 2028 ([Sidley](https://datamatters.sidley.com/2026/06/22/eu-lawmakers-reach-provisional-agreement-to-delay-key-eu-ai-act-obligations/)). The GPAI Code of Practice has about 28 signatories; Meta declined. | A binding risk-based approach, now with "simplification" pressure. | 2026-08 |
| **UK: PM Andy Burnham (since 20 Jul 2026); AI Minister Kanishka Narayan (cabinet-level); Business, Innovation, Science and Trade Secretary Jonathan Reynolds** | 2 | S, R | Burnham abolished DSIT, merged it into a new business department, and created the first cabinet-level AI minister ([Bloomberg Law](https://news.bloomberglaw.com/artificial-intelligence/burnham-appoints-first-ai-minister-to-cabinet-in-tech-reshuffle)). Runs AISI (see 2.4). No frontier AI bill as of this note **[nr]**. | Focus on "middle powers" cooperation on AI security ([ARY](https://arynews.tv/uk-collaborates-on-global-ai-security-efforts)). | 2026-08 |
| **India: PM Narendra Modi; Minister of Electronics and IT Ashwini Vaishnaw** | 2 | S, C | Hosted the AI Impact Summit (New Delhi, Feb 2026), which produced the New Delhi Declaration ([Fortune](https://fortune.com/2026/02/23/indias-ai-impact-summit-closes-with-the-new-delhi-declaration-and-a-200-billion-boost/)). IndiaAI Mission has more than 38k subsidised GPUs. Governance guidelines from Nov 2025 take a "techno-legal" approach, with a network of safety institutes ([Tribune](https://www.tribuneindia.com/news/world/ai-impact-summit-2026-indias-ai-governance-guidelines-anchored-by-seven-sutras-to-drive-safe-trusted-innovation/)). | Diffusion first, with light-touch regulation. | 2026-05 |
| **UAE: Sheikh Tahnoon bin Zayed (National Security Adviser; chairs G42 and MGX) [nr]; G42 (CEO Peng Xiao [nr])** | 1 | K, C | MGX is a Stargate equity partner. Stargate UAE is 1 GW within a planned 5 GW campus, operated by OpenAI and Oracle. A US–UAE framework allows up to 500k advanced chips a year ([The National](https://www.thenationalnews.com/future/technology/2025/11/20/uae-ai-nvidia-chips-us/)). Co-hosts the 2028 AI summit. | Pro-build. Accepted US security conditions. | 2026-02 |
| **Saudi Arabia: Crown Prince Mohammed bin Salman; PIF; Humain [nr for leadership]** | 2 | K, C | Humain cleared for 35k GB300-equivalents and plans 600k Nvidia chips ([The National](https://www.thenationalnews.com/future/technology/2025/11/20/uae-ai-nvidia-chips-us/)). | Pro-build. | 2025-11 |
| **Japan: PM Sanae Takaichi [nr]; AI Strategic Headquarters** | 2 | R, K | AI Promotion Act, with the first AI Basic Plan adopted Dec 2025 and a phase II draft in June 2026 ([Cabinet Office draft](https://www8.cao.go.jp/cstp/stmain/20260619ai/aiplan_2601_draft_en.pdf)). SoftBank is Japanese. Japan AISI. | Promotion before regulation. | 2026-06 |
| **South Korea: President Lee Jae-myung [nr]** | 2 | R, H | AI Basic Act in force since 22 Jan 2026, with a grace period for fines ([Cooley](https://www.cooley.com/news/insight/2026/2026-01-27-south-koreas-ai-basic-act-overview-and-key-takeaways)). Home of Samsung and SK hynix, the HBM chokepoint. | Comprehensive but promotion-leaning. | 2026-07 |
| **France: President Emmanuel Macron [nr]; G7 presidency 2026 (Évian)** | 2 | K, S | Champions Mistral and hosted the Paris AI Action Summit (Feb 2025). G7 Évian work continued revising the Hiroshima AI Process Reporting Framework ([G7 France brochure](https://online.flippingbook.com/view/264648758/37/)). | Pro-sovereignty and pro-innovation. | 2026 |
| **Taiwan (government)** | 2 | H, X | Hosts TSMC. Its export rules and its security shape all frontier compute. | — | [nr] |
| **Netherlands (government)** | 2 | X, H | Licenses ASML exports. | — | [nr] |
| **Malaysia, Singapore, Thailand** | 3 | X | Transit and data-centre hubs. Malaysia requires permits for US-origin AI chips ([DCD](https://www.datacenterdynamics.com/en/news/malaysian-govt-introduces-export-license-and-30-day-notification-requirement-for-export-of-us-ai-chips/)). | — | 2025-07 |
| **Switzerland (President Guy Parmelin; Geneva AI Summit 2027 delegate Fabiola Gianotti)** | 2 | S | Hosts the next summit in the series, focused on international law ([admin.ch](https://www.admin.ch/en/newnsb/YZYU1gmqW9vcPFMl2VroY); [Netzwoche](https://www.netzwoche.ch/news/2026-08-12/bundesrat-bestimmt-delegierte-fuer-geneva-ai-summit-2027)). | Rules-based governance. | 2026-08 |

### 2.4 Tier 2 — regulators, AI safety and security institutes, evaluators

| Actor | Lever(s) | What they control / why it matters | Stated position | Info date |
|---|---|---|---|---|
| **US CAISI (Center for AI Standards and Innovation, NIST)** — Acting Director **Arvind Raman** (NIST Director) after Chris Fall resigned in Jul 2026 ([Axios](https://axios.com/2026/07/20/trump-ai-security-agency-head-resigns)) | S | US government's frontier model testing, mainly for national-security risks (cyber, bio, chem) and foreign-model assessment. Renamed from the US AI Safety Institute in 2025. No permanent director was found as of Nov 2026. | Focus on "standards and innovation", national security and countering "burdensome" foreign rules. | 2026-07 |
| **UK AI Security Institute** — Director **Henry de Zoete** (from Aug 2026), CTO **Jade Leung**, Chair **Ian Hogarth**, research director Chris Summerfield ([Magica](https://magica.com/news/henry-de-zoete-appointed-director-uk-ai-security-institute); [UKTN](https://uktech.news/ai/ai-security-institute-adds-new-executives-to-top-team-20260821)) | S | The best-funded government evaluator. Runs pre-deployment testing with leading labs. Founding director Oliver Ilott became interim DG for AI. | Security framing: misuse, loss of control, societal resilience. | 2026-08 |
| **EU AI Office** | R, S | Supervises GPAI models with systemic risk. Can request information and run evaluations from Aug 2026. | Binding compliance regime. | 2026-08 |
| **China AI Safety and Development Association (CnAISDA)** | S, V | China's counterpart to the safety institutes, launched Feb 2025 ([China Briefing](https://www.china-briefing.com/news/china-ai-regulation-2026-enforcement-guidance-compliance/)). Its channel into international dialogue. | Development and safety framed together. | 2025-02 |
| **Japan AISI, Korea AISI, Canada AISI, Singapore Digital Trust Centre, India's AISI network, International Network of AI Safety Institutes [nr]** | S | Smaller evaluators. The network is a coordination point. | Varies. | [nr] |
| **Third-party evaluators (METR, Apollo Research, others) [nr]** | S, V | Pre-deployment evaluations that labs cite in system cards. Anthropic published "An update on independent evaluators" on 15 Oct 2026 ([Anthropic news](https://www.anthropic.com/news)). | Evidence-based capability and risk measurement. | 2026-10 |

### 2.5 Tier 1–2 — capital

| Actor | Lever(s) | What they control / why it matters | Stated position | Info date |
|---|---|---|---|---|
| **SoftBank (Masayoshi Son)** | K, C | Reported $30–40B in OpenAI across 2025–26, funded in part by selling its entire Nvidia stake. Chairs Stargate ([eWeek](https://www.eweek.com/fr/news/softbanks-40b-openai-deal/); [Euronews](https://euronews.com/business/2025/01/30/softbank-set-to-invest-billions-extra-in-stargate-co-partner-openai)). Figures differ across sources. | Son has said he wants superintelligence ("ASI") within about a decade **[nr]**. | 2026-02 |
| **Gulf sovereign capital: MGX (Abu Dhabi), PIF, QIA** | K | Fund the largest rounds. Reports in Jan 2026 described OpenAI pitching Middle East investors for a raise of about $50B ([AGBI](https://www.agbi.com/ai/2026/01/openai-meets-middle-east-investors-for-50bn-fundraising/)). | Pro-build. | 2026-01 |
| **Hyperscaler balance sheets (Microsoft, Alphabet, Amazon, Meta, Oracle)** | K, C | 2026 capex runs in the hundreds of billions; Meta alone is reported at $115–135B (secondary, [Fortune](https://fortune.com/2026/04/08/meta-unveils-muse-spark-mark-zuckerberg-ai-push/)). | — | 2026 |
| **Public equity markets (after the IPOs)** | K | SpaceX listed in Jun 2026. Anthropic's public S-1 came on 26 Oct 2026, and OpenAI filed confidentially in Jun 2026. From 2027, ordinary index investors and the SEC become part of the capital lever, and quarterly earnings pressure starts to apply to frontier labs. | — | 2026-10 |
| **a16z (Marc Andreessen, Ben Horowitz)** | K, V | Major backers of Leading the Future, which reportedly spent more than $8M against pro-regulation NY candidate Alex Bores ([LDS](https://letsdatascience.com/news/ai-super-pacs-duel-over-midterm-spending-894242e9)). | Openly accelerationist ("techno-optimist") **[nr for wording]**. | 2026-10 |
| **Coefficient Giving (formerly Open Philanthropy; CEO Alexander Berger)** | K, V | The largest funder of AI safety research and policy. Renamed in Nov 2025, now runs multi-donor funds, and gave more than $1B in total in 2025 (secondary: [LongtermWiki](https://www.longtermwiki.com/organizations/coefficient-giving)). Berger expects IPO wealth from AI labs to add about $40B a year to US philanthropy ([TNW](https://thenextweb.com/news/coefficient-giving-ai-safety-funding-ipo-correlation)). | Funds risk reduction. | 2026 |
| **Lab-linked philanthropy: OpenAI Foundation (~26% of OpenAI Group); Anthropic co-founders' 80% wealth pledge; Anthropic's "Investing in the public benefit" (18 Oct 2026)** | K | May become the largest pools of AI-governance money anywhere once the IPOs happen ([Gizmodo](https://gizmodo.com/anthropic-ceo-worries-humanity-may-not-be-mature-enough-for-advanced-ai-2000714187); [Anthropic news](https://www.anthropic.com/news)). | Mission-aligned. Independence from the parent lab is an open question. | 2026-10 |

Funders in more detail, such as the Survival and Flourishing Fund, FLI and Schmidt Sciences, belong in the ecosystem note.

### 2.6 Tier 2 — international bodies and processes

| Body | Lever(s) | What it controls / why it matters | Status | Info date |
|---|---|---|---|---|
| **UN Independent International Scientific Panel on AI** — 40 members, terms 12 Feb 2026 to 11 Feb 2029; co-chairs **Maria Ressa** and **Yoshua Bengio** ([UN panel members](https://www.un.org/independent-international-scientific-panel-ai/en/panel-members); [Citizen Portal](https://citizenportal.ai/articles/7590777/International/United-Nations/UN-scientific-AI-panel-names-Maria-Ressa-and-Yoshua-Bengio-as-cochairs)) | S, V | An IPCC-style shared evidence base that every UN member can cite. | Presented a preliminary assessment at the first Global Dialogue. | 2026-07 |
| **UN Global Dialogue on AI Governance** | S | All-member forum. The first session met in Geneva on 6–7 Jul 2026, and the second is planned for New York in May 2027 ([IISD](https://sdg.iisd.org/news/global-convenings-advance-ai-governance-call-for-digital-tech-to-benefit-all/)). | Non-binding. Disagreement over "whose rules". | 2026-07 |
| **AI summit series** (Bletchley 2023 → Seoul 2024 → Paris 2025 → New Delhi Feb 2026 → **Geneva 2027** → UAE 2028) | S | Where frontier safety commitments were first made (Seoul, 2024). The emphasis has drifted from safety toward "impact" and diffusion. | Geneva 2027 will focus on international law ([digitalswitzerland](https://digitalswitzerland.com/switzerland-to-host-the-global-ai-summit-2027-in-geneva/)). | 2026-08 |
| **OECD / G7 Hiroshima AI Process** | S | Voluntary reporting framework for advanced AI developers. Submissions received by 1 Sep 2026 feed the next review ([OECD.AI](https://oecd.ai/en/transparency)). | Revision under the French G7 presidency. | 2026 |
| **WAICO (World AI Cooperation Organization)** | S, V | China-led intergovernmental body headquartered in Shanghai, with 29 founding signatories (Jul 2026). | Being set up. Membership list not found. | 2026-07 |
| **US–China AI channel** | S, X | Agreed in principle at the Sep 2026 Washington summit (reported). The only bilateral channel between the two compute superpowers. | Details unverified. A November meeting was reported by one weak source only. | 2026-09 |
| **International AI Safety Report (chair Yoshua Bengio) [nr for 2026 edition]** | S, V | The scientific consensus document for the summit series. | — | [nr] |

### 2.7 Tier 2–3 — biosecurity decision makers

AI-enabled biological risk is the domain where frontier labs' own safeguards are most developed and where physical chokepoints still exist.

| Actor | Lever(s) | What they control / why it matters | Status / position | Info date |
|---|---|---|---|---|
| **DNA synthesis providers (Twist Bioscience, IDT/Danaher, GenScript and others) and the International Gene Synthesis Consortium (IGSC, 40+ members)** | B | Turning a digital sequence into physical DNA is the most enforceable chokepoint between AI-assisted design and a real pathogen. IGSC members screen orders under a Harmonized Screening Protocol. | A 2025 *Science* red-team study (Microsoft-led, with Twist and IGSC) found that AI-reformulated toxins evaded screening, and patches followed ([Business Wire](https://www.businesswire.com/news/home/20251002385305/en)). Screening is voluntary for most providers. | 2025-10 |
| **Benchtop DNA synthesiser makers [nr]** | B | Desktop synthesis could bypass centralised screening. | Proposals to require built-in screening ([AEI](https://ctse.aei.org/why-universal-gene-synthesis-screening-protects-american-biotech/)). No binding rule found. | 2026 |
| **IBBIS (Swiss non-profit) and the DNA Screening Standards Consortium** | B, S | Free screening software and standards. Manages tiered access to hazardous-variant data ([EurekAlert](https://www.eurekalert.org/news-releases/1100008)). | Active. | 2025-11 |
| **US OSTP / NSTC (gene synthesis framework under EO 14292)** | B, R | EO 14292 (May 2025) ordered a revised nucleic-acid screening framework within 90 days. A Senate letter in Jun 2026 asked whether it had been done ([Ossoff letter](https://www.ossoff.senate.gov/wp-content/uploads/2026/07/26.06.24_OSTP-AI-Letter.pdf)). | Appears overdue. The 2024 framework's review date passed on 13 Oct 2026. | 2026-06 |
| **US Congress: S. 3741, Biosecurity Modernization and Innovation Act (Sen. Tom Cotton, introduced 29 Jan 2026)** | B, R | Would require synthesis providers to screen orders and customers ([govinfo](https://www.govinfo.gov/content/pkg/BILLS-119s3741is/xhtml/BILLS-119s3741is.html); [CRS](https://www.everycrsreport.com/files/2026-07-16_IF13269_753d0316d2bb9ed4d75d363e287bcacbf13b40fb.html)). | Not enacted as of Jul 2026. | 2026-07 |
| **Biological Weapons Convention Working Group** | B, S | Working toward compliance and verification, S&T review and cooperation mechanisms. The 9th session ended on 21 Aug 2026 with most text provisionally agreed; WG10, the last session, runs **7–11 Dec 2026** before the 10th Review Conference in 2027 ([CBW Events daily reports](https://www.cbw-events.org.uk/BWC26-12.pdf)). | A real decision point within weeks. | 2026-08 |
| **WHO (Director-General Tedros Adhanom Ghebreyesus [nr]); Pandemic Agreement process [nr]** | B, S | Global outbreak response and norms on dual-use research. | — | [nr] |
| **Frontier labs' bio safeguards** | B, T | Anthropic's ASL-3 protections, its Life Sciences Verification Program (17 Sep 2026), and OpenAI's Preparedness "High" bio threshold decide who gets uplift. | Anthropic: verification-gated access for life-science users ([Anthropic news](https://www.anthropic.com/news)). | 2026-09 |

### 2.8 Tier 2–3 — influential voices (where they shape decisions)

These people matter only to the extent that they move the actors above. The test for inclusion is a documented channel to decisions: a formal role, testimony, or a coalition that changed a policy.

| Voice | Channel to decisions | Position (source) | Info date |
|---|---|---|---|
| **Yoshua Bengio** | Co-chair of the UN Scientific Panel. Chair of the International AI Safety Report **[nr for 2026]**. | Signed the Superintelligence Statement. Warns that frontier AI could surpass most people on most cognitive tasks within a few years ([FLI](https://futureoflife.org/press-release/prominent-scientists-faith-leaders-policymakers-and-artists-call-for-a-prohibition-on-superintelligence/)). | 2026-03 |
| **Geoffrey Hinton** | Public and elite opinion, as a Nobel laureate. | Signed the call for a prohibition on superintelligence until there is scientific consensus that it can be done safely and strong public buy-in (same source). | 2025-10 |
| **Future of Life Institute (Max Tegmark)** | Coalitions, the Superintelligence Statement, and lobbying. | The statement had thousands of signatories, with counts that vary ([FLI](https://futureoflife.org/press-release/prominent-scientists-faith-leaders-policymakers-and-artists-call-for-a-prohibition-on-superintelligence/)). Tegmark: it is not a general pause, only on systems that could escape human control. | 2025-10 |
| **Maria Ressa** | Co-chair of the UN Scientific Panel. | Information-ecosystem harms. | 2026-03 |
| **Zico Kolter** | Chairs OpenAI's Safety & Security Committee, which can halt releases. | Discusses bio, cyber and self-improvement thresholds ([SecurityWeek](https://www.securityweek.com/who-is-zico-kolter-a-professor-leads-openai-safety-panel-with-power-to-halt-unsafe-ai-releases/)). | 2026-05 |
| **AI super PAC networks: Leading the Future (Brockman, a16z) vs Public First (Anthropic-aligned)** | Elections. About $53M of independent expenditure through late September 2026 ([FourWeekMBA FEC analysis](https://fourweekmba.com/ai-anthropic-allies-vs-a16z-ai-super-pacs-have-spent-53m/)). | Against regulation vs for guardrails and transparency. | 2026-10 |
| **Other researchers and voices (Stuart Russell, Yann LeCun, Eliezer Yudkowsky/MIRI, Ilya Sutskever) [nr]** | Varies. | Span the range from "AI risk is overblown" to "stop now". | [nr] |

---

## 3. Notes on positions: what the record shows

- **The labs most worried about risk are also building fastest.** Anthropic's CEO calls AI a civilisational "test" while raising capital at a reported valuation of nearly $1T and filing to list. OpenAI publishes a target date for an automated AI researcher. Several have said they want governments to slow everyone down together, but none says it will slow down alone. Anthropic's RSP v3 makes this explicit by separating what it can do unilaterally from what needs industry-wide action ([Anthropic](https://anthropic.com/news/responsible-scaling-policy-v3)).
- **The US government's revealed position is acceleration plus control of access:** it relaxes domestic constraints (preemption push, CAISI rebranded around "innovation") and manages foreign access (licences, tariffs, volume caps). The Pentagon dispute with Anthropic shows the state will push back on vendor-imposed limits on use ([Bloomberg Law](https://news.bloomberglaw.com/bloomberg-government-news/pentagon-notifies-lawmakers-anthropic-is-a-supply-chain-risk)).
- **China's stated position is now more safety-literate on paper.** The 15th Five-Year Plan has life-cycle risk management, CnAISDA exists, and WAICO is being set up. China's operating regime is also more prescriptive at deployment, through labelling and filing. It is less clear whether any of this binds frontier training.
- **The EU is the only jurisdiction with live, binding GPAI enforcement**, and it is also delaying other parts of its Act.

---

## 4. Keeping the list current

### 4.1 Sources, by reliability

| Source type | Use for | Examples |
|---|---|---|
| Primary filings | Ownership, voting control, board power, financials | SEC EDGAR (Anthropic S-1, SpaceX S-1, Alibaba 6-K); HKEX filings for Zhipu, MiniMax and Moonshot |
| Official registers | Rules and their dates | Federal Register / BIS; EUR-Lex and the AI Office's digital-strategy pages; CAC notices; gov.uk; UN panel pages |
| Company governance pages | Leaders, boards, safety frameworks | anthropic.com/news, the RSP changelog, OpenAI board and Preparedness pages, DeepMind Frontier Safety Framework |
| Specialist trackers | Compute and concentration | [Epoch AI](https://epoch.ai/data-insights/largest-data-center-compute) data-centre hub (covers about 26% of global AI compute as of Mar 2026), CSET ETO AGORA, OECD.AI, IAPS |
| Specialist newsletters | China and bio | AI Safety in China; CBW Events BWC reports; Transformer |
| Wikis | Leads only | LongtermWiki says it has *not been actively maintained since May 2026*, so do not use it for current roles |

**Weak-source warning:** many 2026 search results come from aggregator, crypto-news or machine-written sites with inconsistent figures (valuations especially). The pipeline should require one primary or tier-one press source before changing any Tier 0 or Tier 1 row.

### 4.2 Signals that should trigger an update

- **Leadership changes:** CEO, chair, chief scientist, head of safety, or a regulator's director. In 2026 alone: DeepMind (Aug), UK AISI (Aug), CAISI (Jul), UK PM (Jul), OpenAI's COO and CRO.
- **Governance instruments:** a new RSP, Preparedness or FSF version; changes to board or trust powers; IPO prospectuses (dual-class structures that move power to founders).
- **Compute events:** a new largest cluster (Epoch's record doubles about every seven months), new mega-deals measured in GW, chip export licences.
- **Legal events:** enforcement start dates such as EU GPAI on 2 Aug 2026; court rulings such as Anthropic v. Department of War; federal preemption votes.
- **Geopolitical events:** US–China summits, new entity listings, Taiwan Strait signals, Gulf chip approvals.
- **Bio events:** BWC WG10 (7–11 Dec 2026) outcome, the OSTP framework, S. 3741 progress.
- **Election results:** US midterms of 3 Nov 2026, now being counted; California governor.

### 4.3 Update cadence

| Layer | Cadence |
|---|---|
| Tier 0 and Tier 1 person-in-role checks | Monthly, plus within 48 hours of any trigger above |
| Stated-position quotes | Quarterly, and whenever a new framework version is published |
| Full re-tiering | Every six months, with a visible changelog ("moved from Tier 2 to Tier 1 because…") |
| Compute concentration figures | When Epoch updates, roughly monthly to quarterly |

Each row should store: `actor_id`, `institution`, `person`, `role`, `levers[]`, `tier`, `tier_confidence`, `stated_position`, `position_source_url`, `position_date`, `verified_on`, `verified_by`, `source_quality` (primary / press / secondary). Mark any row as stale in the UI once `verified_on` is older than 90 days.

---

## 5. How to display it

1. **Map of power (default view).** A world map with nodes sized by tier and coloured by lever. The visual point is clustering: most Tier 0 and Tier 1 nodes sit on the US West Coast, Washington DC, Hsinchu, Veldhoven, Icheon/Suwon, Beijing/Hangzhou and Abu Dhabi.
2. **Supply-chain river (Sankey).** ASML → TSMC (+ HBM from SK hynix, Samsung, Micron) → Nvidia / TPU / Trainium / Ascend → hyperscalers, SpaceXAI and Stargate → labs → deployment. Mark export-control "gates" on the links. This shows why a few upstream firms are chokepoints.
3. **Network graph.** Edges for ownership (Microsoft–OpenAI 27%, Google and Amazon–Anthropic, SoftBank–OpenAI, Alibaba–Moonshot), compute contracts (Anthropic–Google 5 GW, Anthropic–Amazon, OpenAI–Oracle/Stargate), government contracts (Department of War deals), funding and personnel moves. Readers can see, for example, that Amazon, Google and SpaceXAI all supply compute to Anthropic.
4. **"Who could pause this?" view.** Columns for each kind of pause:
   - *Pause one lab's next frontier run:* that lab's CEO and board (the LTBT majority at Anthropic; the OpenAI Foundation board and the Safety & Security Committee at OpenAI; Alphabet's leadership; Musk alone at SpaceXAI; Zuckerberg at Meta).
   - *Pause all US frontier training:* the US President (through emergency powers and export rules, legally untested) or Congress. In practice, also the four or five compute owners acting together.
   - *Cap global compute growth:* TSMC, ASML and the HBM makers (technically), or the US, Dutch, Taiwanese, Korean and Japanese governments (legally).
   - *Pause Chinese frontier training:* the CCP leadership alone.
   - *Pause globally:* only a US–China agreement plus chip-supply enforcement. Today the only bilateral channel is the AI dialogue reported in Sep 2026.
   Show for each veto point whether it has ever been used. For example, the OpenAI board fired Altman in Nov 2023 and reversed itself within days; the Pentagon used procurement power against Anthropic in 2026.
5. **Concentration meters.**
   - Share of global AI compute held by the top five firms: about 66–71% (Epoch-based, secondary; [Pulse](https://www.pulse.bot/ai/blogs/five-hyperscalers-now-own-over-two-thirds-of-global-ai-compute-ed463af3-ec81-4b8c-8c71-f5caff392c9d/)).
   - Number of organisations that own a cluster within 2x of the largest: about five (Epoch).
   - Share of CoWoS packaging used by AI chip designers: the top four took about 90% in 2025 (Epoch, via secondary).
   - Number of individuals with unilateral authority to start or stop a frontier run, estimated at 10 to 20 worldwide. Present it as a range, never a point.
   - A Herfindahl index over frontier compute shares, with the uncertainty band shown.
6. **Timeline of "who changed".** A dated changelog for each row, which also supplies the news-pipeline note.

---

## 6. What an alien would find most striking

1. **Very few hands.** Building frontier compute runs through one lithography firm (ASML), one leading foundry (TSMC), one dominant accelerator designer (Nvidia), and three memory makers. Five organisations own the largest clusters. An observer would count perhaps **10–20 people** whose personal decisions could start or stop the next frontier training run, and two governments that could stop all of them.
2. **The leading builders say they are worried about what they are building.** Several heads of frontier labs say publicly that the technology could be catastrophic. All are scaling as fast as capital allows, and each points to the others as the reason.
3. **The control structures are being tested and reshaped in public.** Nonprofit and trust structures were built to restrain profit motives (the OpenAI Foundation, Anthropic's LTBT). They are now being carried into public markets with dual-class shares, which move voting power to founders and push quarterly earnings pressure onto the labs.
4. **Safety institutions are thin compared with the labs they test.** The US federal AI testing body had an acting head on loan from NIST for most of the second half of 2026. The UK's institute changed directors twice in a year. The labs being tested each spend more on compute in a week than these institutes' annual budgets **[order-of-magnitude judgement, not a measured figure]**.
5. **Governance is splitting into rival systems.** There is a UN track (panel and dialogue), a China-led WAICO, a G7/OECD track, a summit series that has drifted from "safety" to "impact", and US bilateral deals. None of them binds frontier training.
6. **The most enforceable physical brake in biosecurity is still voluntary.** DNA synthesis screening is mostly self-regulated, and the US replacement framework appears overdue. A treaty decision point, BWC WG10, comes in December 2026.
7. **Military use is being decided by contract.** Terms for frontier AI on top-secret networks were set in procurement deals in 2026. The one lab that insisted on use limits was labelled a supply-chain risk.
8. **Money now reaches elections directly.** Rival AI-industry super PAC networks spent tens of millions of dollars in the 2026 US midterms. An alien would note that the industry is now spending to choose the people who would regulate it.

---

## 7. Cross-references

- Dashboard indicators (compute concentration index, safety institute capacity, BWC status): see the indicators note.
- Timelines and pacing (OpenAI's automated-researcher target, Epoch's doubling of the largest cluster every seven months): see the progress and pacing note.
- Ecosystem of orgs and funders (Coefficient Giving fund structure, SFF, FLI, evaluators): see the ecosystem note.
- News pipeline (the trigger list in 4.2 as alert rules; source-quality gating): see the news-pipeline note.

---

## 8. Not verified for this note (open items)

- **2026 US midterm results** (3 Nov) and the California governor race: no results found yet.
- **Permanent CAISI director**: none found after Chris Fall resigned in July 2026.
- **EU AI Office director**: Lucilla Sioli is named by one podcast source only.
- **Current-year statements** from Jensen Huang, Elon Musk, Mark Zuckerberg, Sam Altman (beyond the Oct 2025 roadmap) and Demis Hassabis on pacing: not refreshed.
- **Exact valuations** (Anthropic's $965B, OpenAI's 2026 round, Mistral's €20B, Moonshot's $50B+): aggregator sources disagree.
- **Outcome of Anthropic's lawsuit** against the Department of War after Sep 2026.
- **Official text of the US–China AI channel** agreed in Sep 2026.
- **Status of NY RAISE Act amendments, SB 53 enforcement, and any DOJ suits** against state AI laws.
- **Leaders tagged [nr]** (TSMC, ASML, Samsung, SK hynix, Alibaba, DeepSeek, Gulf entities, WHO, Japan, Korea and France heads of government): roles believed current from mid-2026 knowledge, not re-checked.
