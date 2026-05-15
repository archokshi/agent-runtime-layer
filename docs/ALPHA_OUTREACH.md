# Alpha Outreach — Templates & Feedback Guide

---

## Outreach Email (send this)

**Subject:** You're in — try Agentium before anyone else

Hi [Name],

I've been building Agentium — a profiler and control plane for coding agents
(Claude Code, Codex). It shows you exactly what each agent run costs, where
it stalls, and trims 30–45% of redundant tokens automatically.

You're one of the first people I'm giving access to. One command installs
everything:

```
curl -sSL https://agent-runtime-layer.vercel.app/install.sh | bash
```

Docker is handled automatically. Dashboard opens at localhost:4001.

Takes 5 minutes to get your first real trace:
https://agent-runtime-layer.vercel.app/quickstart

The only ask: 10 minutes of feedback after you've run it. I'll send a short
form, or we can do a quick call — whatever works for you.

Questions? Reply here or email optiinfra@gmail.com.

— Alpesh

---

## Follow-up (send 48h later if no response)

**Subject:** Re: Agentium alpha — any blockers?

Hey [Name], just checking in — did the install work?

If anything broke on setup, I want to fix it before you spend more time on it.
Reply with what you saw and I'll sort it out quickly.

---

## Feedback Form (send after they've run it)

You can use a Google Form or Typeform with these questions. Keep it under
10 questions — respect their time.

### Section 1 — Install
1. Which OS did you use? (macOS / Linux / Windows WSL / Windows PowerShell)
2. Did the install command work on the first try? (Yes / No — if no, what happened?)
3. How long did setup take? (Under 2 min / 2–5 min / 5–10 min / Over 10 min)

### Section 2 — First trace
4. Did you connect your agent (Claude Code / Codex) or use the demo trace?
5. Did a run appear in the dashboard? (Yes / No)
6. What was the first thing you looked at in the dashboard?

### Section 3 — Value
7. What did you learn about your agent that you didn't know before?
   (Open text — most important question)
8. Did you enable any optimizations (Context Optimizer / Budget Governor)?
   If yes: did the before/after numbers look right?
9. Would you pay for this? If yes, what tier makes sense for you?
   (Free / $49 Pro / $149 Team / Not yet)

### Section 4 — Friction
10. What was the most confusing or broken thing you hit?
    (Open text — second most important question)

---

## What to do with feedback

| Signal | Action |
|---|---|
| Install failed on a specific OS/step | Fix install.sh or index.html, re-send link |
| No runs appearing (hooks not firing) | Debug hook install path, add troubleshooting step to QUICKSTART |
| Dashboard confusing | Note the specific page — UX fix in v3 |
| "Would pay" → Pro or Team | Prioritize Stripe integration |
| "Would not pay yet" → why? | Dig in — is it missing data, unclear value, or wrong audience? |

---

## Tracking

Keep a simple log: name, OS, install worked (Y/N), first blocker, would pay (Y/N).
Five responses is enough to find the pattern.
