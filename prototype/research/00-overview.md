# 00 · Overview: Earth, seen by an alien judge

*Research note for Dragonfly's "AI and everything" civilisational dashboard. Compiled 2026-11-06 from the five notes in this folder. Each number below is dated and sourced in the note it comes from. Treat any figure marked secondary or unverified there as a lead until it has been checked.*

## The frame

Imagine a decision-maker from elsewhere looking down at Earth and judging whether the transition to advanced AI is going well. They don't need the news. They need answers to five questions:

1. **How fast is it moving?** How capable are the systems, how quickly are they improving, and when do people expect the decisive thresholds? → [03](03-progress-and-pacing.md)
2. **Is steering keeping up with building?** That means alignment, misuse defences, AI welfare, preservation, and whether everyone's interests count. → [01](01-dashboard-design.md), [04](04-ecosystem.md)
3. **Who is deciding?** Whose choices could start, steer or stop it? → [02](02-key-decision-makers.md)
4. **Could anyone slow down if they had to?** What brakes exist and which have actually been used? → [03](03-progress-and-pacing.md)
5. **What changed since last time, and does it move the verdict?** → [05](05-news-pipeline.md)

The judge also needs a baseline: is Earth otherwise getting better or worse on wellbeing, conflict and nuclear risk, climate, pandemics, and governance? That covers the risks AI could add to or help reduce. → [01](01-dashboard-design.md)

## The parts, kept separate

| File | What it is | Main display |
|---|---|---|
| [01 · Dashboard design](01-dashboard-design.md) | For each topic on the "Making things go well" page, plus Meta and the baseline: the key questions, indicators with data sources and latest values, what to do where nothing is measured, and a survey of about 25 existing trackers | A verdict sentence plus status tiles (state, trend, confidence, spread of panel ratings, data freshness) |
| [02 · Key decision makers](02-key-decision-makers.md) | Labs, governments, safety institutes, the chip chain, capital, international bodies, biosecurity, influential voices; tiered by the levers each controls | A map of power, a supply-chain diagram, a "who could pause this?" view |
| [03 · Progress and pacing](03-progress-and-pacing.md) | Capability, compute and investment trends; benchmark saturation; forecasts and how they have moved; whether safety keeps pace; every pause or slowdown mechanism and its status | A speedometer, doubling-time charts, a forecast fan, a pause-status board (P0–P4) |
| [04 · Ecosystem](04-ecosystem.md) | The organisations, agendas, funding flows, headcount and communities working on steering, and which areas are neglected | A steering-vs-building ratio, a funding Sankey, a neglectedness heat map |
| [05 · News pipeline](05-news-pipeline.md) | Sources, LLM triage with a significance rubric, editorial review, formats, cost, legal and safety risks | A daily or weekly "state of the world" brief and a "what changed" log tied to indicators |

## What the judge would notice first (as of 2026-11-06)

- **Progress sped up in 2026.** Epoch's capability index frontier rose faster than its long-run rate. Training compute grows about 5× a year, and AI task length doubled about every 3 months until METR's gauge stopped working above about 16 hours. Most famous benchmarks now saturate within one to two years. (03)
- **Expected dates moved about three years closer in a year.** Metaculus "strong AGI" now sits around September 2030, down from 2033 a year earlier. Panel forecasts keep being overtaken by events. (03)
- **Steering gets roughly 1/400 of what building gets.** Philanthropic safety money was about $0.6B in 2025, with perhaps $1.5–2B in 2026. Hyperscaler capex for 2026 is about $720–830B. The field has roughly 1,100–1,800 full-time people. (04, 03)
- **Very few hands hold the frontier.** The chip chain runs through ASML, TSMC, Nvidia and three memory makers. Five companies own the largest clusters. Perhaps 10–20 people could start or stop a frontier training run, and two governments could stop all of them. (02)
- **No binding brake exists. The real pauses so far were voluntary and short.** Written lab pause pledges weakened in 2026, yet OpenAI paused training twice after containment incidents, and Anthropic withheld a model from general release. Export controls are the only measure that actually slows anyone. The EU delayed its high-risk rules, and the US has no federal AI statute. Proposed status: P0 (racing), with some lab-level holds (P1). (03, 02)
- **The labs are moving into public markets.** SpaceX absorbed xAI and listed. Anthropic filed to go public in October, and OpenAI has filed confidentially. Big safety-oriented pledges from founders and foundations are tied to those listings. (02, 04)
- **The worst blind spots are on the defence side.** Nobody measures how much DNA synthesis is screened. Lab weight security has never been independently audited. AI welfare has almost no data and gets the least governance attention of any risk area surveyed. (01, 04)
- **The baseline is mixed.** 2025 had the most state-based conflicts since 1946, New START expired in February 2026, and the Doomsday Clock is at 85 seconds. Recent years averaged more than 1.5 °C of warming. Child mortality is still falling, but more slowly. (01)
- **Many trackers have quietly stopped updating:** METR's time-horizon page, AI Lab Watch and the Global Health Security Index. So every number needs a freshness label. (01, 03)

## Main recommendations

1. **Don't publish a single civilisational score.** Lead with a signed, dated verdict sentence and a handful of status tiles that show disagreement and data freshness. Add a quarterly expert panel that includes sceptics, with minority views published. (01)
2. **Keep measured data, lab claims, forecasts and expert judgment visibly apart.** Show confidence bands. Show a broken gauge as broken, not as flat. (01, 03)
3. **Put steering next to building everywhere**, from the funding ratio on the front page down to each topic panel. It is the clearest thing the alien would see, and nobody else shows it. (04)
4. **Treat the pause question as a status board with concrete levels** (P0–P4) and a "days since the last frontier safety pause" counter, rather than prose. (03)
5. **Let news change the dashboard through one route only:** an append-only "what changed" log with human sign-off, scored by "if the alien missed this, how wrong would its picture be in a year?" (05)
6. **Start small.** Topics where data already exists come first: Epoch, METR, Our World in Data, CISA, NOAA. A phase-1 news pipeline is estimated at under $100 a month in model costs. Editor time (30–60 minutes a day) is the real cost. (05)
7. **Dragonfly's niche is the parts no one else maps**: AI welfare, preservation, broad participation, power concentration. Disclose Dragonfly's own funding. (04)

## Open questions for Maxim

- **Audience and tone.** Is the site for the public, for decision makers, or for the field? This decides how much is a calm verdict and how much is a live feed.
- **Judgment.** Who signs the verdict sentence, and who sits on the expert panel?
- **Scope of "everything".** Should the baseline layer (climate, conflict, health) be on the dashboard itself or only linked?
- **Neutrality about Anthropic.** The pipeline would use Claude, which is made by Anthropic, a company the site covers. 05 proposes safeguards; is that acceptable, or should triage use another model family?
- **Where it lives.** It could be a section of the Dragonfly site, a separate site, or the overview page grown up.

## Checks still needed before anything is published

The research agents flagged several figures they could only confirm from secondary sources, and two notes disagree in places. Examples:

- **GPT-6 Astra.** 03 relies on Epoch data and OpenAI posts, while 01 found no OpenAI source for the model.
- **Funding totals** for 2026.
- **Several 2026 office holders.** These are tagged **[nr]** in 02.

Each note ends with its own list of what could not be verified. The shared web-search budget also ran out near the end of the research, so some gaps were left open rather than guessed.
