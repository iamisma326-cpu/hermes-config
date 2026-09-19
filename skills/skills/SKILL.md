---
name: skills
description: Skill from jakubkrehel/skills@interface-review
category: design
---

# (no title)
URL: https://raw.githubusercontent.com/jakubkrehel/skills/main/skills/interface-review/SKILL.md

---
name: interface-review
disable-model-invocation: true
description: Reviews your work across multiple categories like UI, typography, layout, color, writing and accessibility and gives you a detailed analysis of the findings.
---

# Change review

This skill reviews a change rather than a screen. It resolves the scope, expands the changed files to the surfaces they affect, reads both sides of the diff and classifies every finding.

Scope is all it owns. Domain rules belong to the `better-*` skills. Severity, consolidation, coverage, the cap and the verdict belong to `better-interface`, which this skill hands the review to.

Correctness, tests, security and performance belong to the project's general code review. Name the concern once and move on.

## The change, not the codebase

The author is asking "did I make this worse?". Report what the change caused and stay mostly quiet about what it merely touched. Three pre-existing findings is a courtesy; thirty is a different review and one nobody asked for.

Read the change before forming an opinion of it. The stated intent decides what counts as incomplete, and a skimmed diff produces findings about code the next hunk already fixed.

## Core principles

### 1. Resolve the change scope first

The whole invocation is the target, so `/interface-review pr 482` reviews pull request 482. [Scope resolution](scope-resolution.md) holds the accepted targets and how each resolves.

With no target supplied, resolve in this order and stop at the first match:

1. `HEAD` is ahead of `git merge-base origin/ HEAD`: that range **plus** any uncommitted changes, with the commit count and the uncommitted file count stated separately.
2. The working tree is dirty: the uncommitted changes.
3. Neither: there is no change to review. Stop and ask, per **With no change, ask rather than invent one**.

Order matters. Check the working tree first and one stray formatting edit shadows a twelve-commit branch, with the report still claiming full coverage.

Exclude lockfiles, snapshots, generated output, vendored code and binaries, and name what you excluded. An empty scope after exclusions reaches the same place by a different route.

### 2. With no change, ask rather than invent one

A clean tree with nothing ahead of the merge base means the user asked to review a change that does not exist. Never fall back to `HEAD~1..HEAD` on your own. The last commit is whatever happened to land, often a merge, often someone else's work, and a report on it is indistinguishable from a report on what the user meant.

State the repository facts you found, then offer the routes and wait. [Nothing to review](scope-resolution.md#nothing-to-review) holds the facts to gather:

- **The last commit**, `HEAD~1..HEAD`, named by short SHA and subject, so the user sees what they would get before choosing it.
- **A target they name**: `pr `, a branch, a ref, or a range, resolved per **Resolve the change scope first**.
- **A whole-repository interface audit
