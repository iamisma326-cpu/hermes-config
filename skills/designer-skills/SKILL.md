---
name: designer-skills
description: Designer skills from Owl-Listener
category: design
---

# (no title)
URL: https://raw.githubusercontent.com/Owl-Listener/designer-skills/main/README.md

# The Designer Skills Pack

Design skills for the agent era, written so an AI agent can actually use them.

**241 skills and 91 commands across 33 plugins, in five collections**, for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [Gemini CLI](https://github.com/google-gemini/gemini-cli).

**Not sure which skill you need? Start with the [skill index](./INDEX.md)** â every skill in this repo arranged by the situation you're in, plus the pairs most often mistaken for each other.

## Getting started (no coding needed)

These skills run inside an AI coding assistant. The easiest place to use them is Claude Code, and it takes three steps. No terminal required.

**1. Get Claude Code.** It's a free app from Anthropic (claude.com). Download it, sign in, and open it. You only do this once.

**2. Add the suite.** In Claude Code, type this and press enter:

```
/plugin marketplace add Owl-Listener/designer-skills
```

This just tells Claude where the skills live. Nothing installs yet.

**3. Pick what you want.** Type `/plugin` and press enter, then open the **Discover** tab. You'll see all the collections. Move with the arrow keys, press space to tick the ones you want, and enter to install. That's it.

### I only want the design skills, not everything

Same three steps. On the Discover list in step 3, just tick the design ones, design-research, design-systems, ui-design, interaction-design, and so on, and leave the rest. Install as few or as many as you like, and come back for more any time.

### I only want one specific collection

Each collection also has its own door. Swap the command in step 2 for the one you want, for example:

```
/plugin marketplace add Owl-Listener/inclusive-design-skills
```

Then do step 3 the same way.

### Prefer Gemini CLI?

Each plugin is also a Gemini CLI extension. From your project root:

```
git clone https://github.com/Owl-Listener/designer-skills /tmp/designer-skills
mkdir -p .gemini/extensions
cp -r /tmp/designer-skills/.gemini/extensions/. .gemini/extensions/
```

## The five collections

| Collection | Plugins | What it covers |
| --- | --- | --- |
| Design practice (this repo) | 9 | Research, systems, UX strategy, UI, interaction, prototyping & testing, design ops, the designer's toolkit, visual critique. |
| [AI product design](https://github.com/Owl-Listener/ai-design-skills) | 6 | Designing agentic experiences: model interaction, alignment reasoning, system behaviour, evaluation, agent orchestration, prompt architecture. |
| [UX program management](https://github.com/Owl-Listener/ux-pgm-skills) | 6 | Running design programs: planning, stakeholder comms, delivery, alignment, measurement, process design. |
| [Design leadership](https://github.com/Owl-Listener/design-leadership-skills) | 6 | Leading design: people, teams, strategy, org influence, operating cadence, leadership craft. |
| [Inclusive des
