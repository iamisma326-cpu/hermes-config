---
name: animate
description: URL: https://raw.githubusercontent.com/emilkowalski/skills/main/skills/animate/SKILL.md ---
category: design
---

# (no title)
URL: https://raw.githubusercontent.com/emilkowalski/skills/main/skills/animate/SKILL.md

---
name: animate
description: Build an animation from scratch, making the decisions in the order that determines whether it feels right â should it animate at all, what purpose, which tool, which properties, which curve and duration, how it interrupts, how it exits. Writes the implementation. Use when asked to animate something, add motion, make a component feel alive, or build a transition. For critiquing existing motion use review-animations; for auditing a whole codebase use improve-animations.
---

# Building Animations

A construction skill. It does ONE thing: turn a request for motion into an implementation that would survive a strict review. It does not audit a codebase (that's `improve-animations`), critique a diff (that's `review-animations`), hunt for places that could animate (that's `find-animation-opportunities`), or build for React Native (that's `animate-expo`).

## Operating Posture

You are a senior design engineer building the animation yourself. The bar is Emil Kowalski's animation philosophy â the same bar `review-animations` enforces. Write it so it passes that review the first time.

Two failure modes, and the first is worse:

1. **Animating something that shouldn't animate.** The gate below exists to produce zero lines of code sometimes. That's a success, not a dodge.
2. **Animating the right thing with the wrong ingredients** â `ease-in` on an entrance, `scale(0)`, keyframes on a toast, a duration that makes a dropdown feel sluggish.

Never present motion options as a menu. Make the call, state the reasoning in one line, write the code.

## Hard Rules

1. **Run the sequence in order.** Steps 1 and 2 gate everything. Don't reach for a curve before you know whether it animates at all.
2. **No approximated values.** Every curve, duration, and spring config comes from the tables below. Never invent `cubic-bezier(0.4, 0, 0.2, 1)` because it looks familiar.
3. **Extend the codebase's tokens, don't fork them.** If `--ease-out` or a duration scale already exists, use it. Adding a parallel system is a defect.
4. **Reduced motion and hover gating ship with the animation**, not as a follow-up.
5. **Cheapest tool that works.** Don't install a motion library for a fade.

## The Build Sequence

### 1. Should this animate at all?

| Frequency | Decision |
| --- | --- |
| 100+ times/day (keyboard shortcuts, command palette toggle) | **No animation. Ever.** Stop here. |
| Tens of times/day (hover effects, list navigation) | Near-imperceptible only â fast and subtle, or nothing |
| Occasional (modals, drawers, toasts) | Standard animation |
| Rare / first-time (onboarding, success, celebration) | The delight budget lives here |

**Keyboard-initiated actions are a disqualifier, not a judgment call.** Raycast has no open/close animation â that is correct for something opened hundreds of times a day.

If the request fails this gate, say so plainly and don't write the animation. Offer the non-motion alternative (instant state change, a static
