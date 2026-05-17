# Agentium — Product Value Proposition

*Working document. Expand as evidence grows.*

---

## The Core Insight

**Coding agents are broken by design.**

95% of every model call is identical tokens — system prompt, tool definitions, repo
summary — re-sent on every single request. Only 5% is new work. Providers charge
full price for all of it.

```
Typical Claude Code session (observed via Agentium):
  Model calls:       ~300 per session
  Input tokens:      ~20M per session
  Repeated tokens:   ~19M (95%)
  New useful tokens: ~1M  (5%)

  API-equivalent cost:  $8–10 per session
  Claude Code Max plan: $0.67/day ($20/month)
```

Developers on $20/month subscriptions are generating $40–100/day in
provider cost — because agents repeat the same context hundreds of times.

---

## The Problem (Three Layers)

### 1. For Developers on Subscriptions ($20/month Claude Code Max)
- The dollar cost isn't real — they pay a flat fee
- But **token consumption hits rate limits and usage caps**
- At 95% repeated context, they're getting **5% of their subscription's potential value**
- Sessions that should run for hours hit limits in minutes

### 2. For Developers Paying Per Token (API users, enterprises)
- The cost IS real — $8–10 per session, every session
- A team of 10 developers running agents = **$400–1000/day** in API costs
- No visibility into where the cost comes from
- No automatic way to fix it

### 3. For AI Providers (Anthropic, OpenAI)
- Subscription economics rely on average usage staying below the subscription price
- Coding agents are extreme outliers — heavy users cost 5–10x what they pay
- Token waste at scale strains infrastructure and erodes subscription margin
- Reducing repeated context = better unit economics for the entire ecosystem

---

## Multi-Directional Value Proposition

### Direction 1 — The $20/Month Subscription User

**The obvious framing (weak):** "You're not paying per token, so cost savings don't apply."

**The real framing (strong):** The subscription user is the *most* frustrated — they can't see the problem at all.

What actually happens:
- They run a long Claude Code session — it **cuts off mid-task** at the rate limit
- They have **zero visibility** into why — no signal about what consumed their quota
- They restart, the agent **rebuilds all context from scratch** — hitting limits even faster
- They feel like the product is "broken" or "unreliable"

**The real value is reliability and session length, not cost.**

95% repeated tokens = hitting rate limits 20x faster than necessary. Fix that and the same $20/month delivers:
- Sessions that **finish** instead of cutting off mid-task
- **More tasks per day** within the same quota
- **Lower latency** — fewer tokens = faster responses per call
- **Better model quality** — less noise = model focuses on what matters

> *"Your $20/month subscription is delivering 5% of its potential. Agentium gives you the other 95%."*

---

### Direction 2 — Large-Scale Teams (Mixed Subscription + API)

**The non-obvious angle: org-level visibility is the real problem.**

A 20-developer team has:
- Some on Claude Code Max ($20/month flat)
- Some using Codex via API (pay per token)
- Some using both

The CTO has **zero visibility** into:
- Which developers are token-efficient vs. wasteful
- Which projects are cost-efficient vs. runaway
- Whether API spend is growing from more usage or from inefficiency
- How to forecast next month's bill

This is a **compliance and forecasting problem** as much as a cost problem.

**The ROI story:**
```
20 developers × 5 sessions/day × $5 avg = $500/day = $180K/year in API costs
Agentium Team tier = $1,800/year
Even 10% reduction = $18K saved = 10× ROI on day one
At −43% reduction = $77K saved = 43× ROI
```

**What teams get beyond cost:**
- **Budget predictability** — stop surprise $50K API bills
- **Team benchmarking** — which workflows need optimization?
- **Risk management** — Budget Governor prevents one runaway agent from burning the monthly budget
- **Audit trail** — every model call logged, critical for regulated industries

---

### Direction 3 — AI Providers (Anthropic, OpenAI, Google)

**This is the most underexplored angle — and possibly the biggest.**

The uncomfortable truth: **the most active users are the worst customers economically.**

```
Heavy Claude Code developer:
  Pays:           $20/month ($0.67/day)
  Costs to serve: ~$100/day in compute
  Loss ratio:     150× on a heavy user
```

Subscription economics only work if average usage stays below the subscription price. Coding agents break this model completely.

**What providers actually want:**
- Token efficiency across their user base
- More users served per GPU
- Subscription economics that don't crater at scale

**Agentium is infrastructure-level help for providers:**
- If Claude Code's heaviest users cut token usage 43%, Anthropic serves more users with the same GPU fleet
- Better subscription margin without raising prices
- Ability to raise usage limits without proportional infrastructure investment

**The strategic question:** Could providers partner with or embed Agentium?
This isn't far-fetched — it's directly aligned with their infrastructure economics.
Agentium works across providers, which no single provider's native caching will.

---

### Direction 4 — Macro / Planetary Scale

**This is where it becomes genuinely important — and where most people stop thinking.**

**The math at global scale:**
```
Global coding agent users (2026, growing):  ~5M active developers
Sessions per developer per day:              ~10
Input tokens per session:                    ~20M
Total tokens processed daily:                1 quadrillion (10^15)

At 95% redundancy:                          950 trillion wasted tokens/day
```

**Energy:**
- H100 GPU: ~700W, processes ~1,500 tokens/second at inference
- 950 trillion wasted tokens ÷ 1,500 tokens/sec = 633 billion GPU-seconds/day
- At 500W average = **317 billion watt-hours = 317 GWh wasted daily**
- Equivalent to the daily power consumption of a mid-sized country

**Water:**
- Data centers use water cooling (~1–2 liters per kWh)
- 317 GWh × 1.5L = **475 million liters of water/day** processing redundant tokens

**Carbon:**
- At ~0.4 kg CO₂/kWh (US grid average):
- 317 GWh × 0.4 = **127,000 tonnes CO₂/day** from wasted tokens alone

**The reframe:**
> Agentium isn't just a developer tool. Fixing token waste at scale is equivalent
> to taking millions of cars off the road — without asking anyone to change behavior.

This is a **sustainability narrative** that no other developer tool can claim.
And it's grounded in real, measured data — not greenwashing.

---

## The Four-Direction Value Map

| Audience | Core pain | Value delivered | Pitch |
|---|---|---|---|
| **$20/month user** | Sessions cut off, agent unreliable | 20× more session headroom, tasks that finish | "Get 100% of your subscription" |
| **Enterprise team** | No visibility, unpredictable API bills | Observability + budget control + audit trail | "Know what you're spending before you spend it" |
| **AI Providers** | Heavy users destroy subscription economics | Token efficiency = better margins, more users per GPU | "We make your best customers sustainable" |
| **Planet** | AI inference energy & carbon cost | 95% compute waste eliminated at scale | "The most efficient AI is one that doesn't repeat itself" |

---

## What Agentium Does

**See it → Fix it → Control it → Remember it**

| Feature | What it does | Who benefits |
|---|---|---|
| **Profiler** | Shows exactly where tokens go, what each session costs, which context repeats | All users |
| **Context Optimizer** | Strips 95% repeated tokens automatically — one toggle | API users (real $ savings), subscription users (more headroom) |
| **Budget Governor** | Caps cost and retries — hooks block runaway agents | Teams, enterprises |
| **Context Memory** | Caches stable context at $0.30/MTok vs $3.00/MTok (10× cheaper) | API users, enterprises |

---

## The Numbers (Measured, Not Estimated)

From live Agentium traces:

| Metric | Value |
|---|---|
| Average repeated context % | **95–99%** |
| Token reduction after optimization | **−43% to −95%** |
| Cost reduction per session | **−43%** (verified) |
| Sessions where repeated CTX > 55% | **10 of 10 in QA run** |
| Avg API-equivalent cost per session | **$0.05–$10 depending on length** |
| GPU-hours wasted globally (est.) | **88M GPU-hours/day** |
| CO₂ from repeated tokens (est.) | **127,000 tonnes/day** |

---

## The Moat

The more you use Agentium, the smarter it gets:
- Context Memory learns which blocks are stable across sessions
- Every run adds to the optimization baseline
- Switching cost = your entire agent history and optimization fabric

Competitors (Langfuse, Helicone, Portkey) offer observability.
**Agentium offers observability + automatic optimization + cost enforcement.**

---

## Strongest Angles (Prioritized)

1. **Near-term revenue:** Enterprise teams on API. ROI is immediate, quantifiable, CFO-friendly.
2. **Subscription user growth:** "Get 100% of your $20/month" — resonates with every Claude Code user hitting limits.
3. **Long-term moat:** Sustainability narrative. No one owns "AI efficiency" as a category yet. Agentium has the data.
4. **Strategic:** Provider partnership potential — Agentium's economics align directly with Anthropic/OpenAI's infrastructure interests.

**Riskiest assumption:** Providers solve this themselves by baking caching into their platforms.
**Counter:** Agentium works cross-provider, adds observability and control no single provider will build, and the optimization fabric compounds with usage history.

---

## Pricing Philosophy

**Free to observe. Pay only when you save.**

| Tier | Price | What unlocks |
|---|---|---|
| Observe | Free | Full dashboard, unlimited traces |
| Pro | Early access pricing | Context Optimizer — trim repeated tokens |
| Team | Early access pricing | Budget Governor — cost caps + retry limits |
| Enterprise | Contact us | Context Memory — persistent cache fabric |

---

*Last updated: 2026-05-17 · Expand with investor data, case studies, and benchmark results.*
