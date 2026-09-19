---
name: frontend-design
description: Guidance for distinctive, intentional visual design when building new UI or reshaping an existing one. Helps with aesthetic direction, typography, and making choices that don't read as templated defaults.
category: frontend
---

# Frontend Design Skill (Anthropic)

## Overview
This skill provides guidance for creating distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. It helps with aesthetic direction, typography, and making intentional design choices.

## When to Use
Use this skill when the user asks to build web components, pages, artifacts, posters, or applications (examples include websites, landing pages, dashboards, React components, HTML/CSS layouts, or when styling/beautifying any web UI).

## Key Principles

### Aesthetic Direction
- Choose a clear conceptual direction and execute it with precision
- Bold maximalism and refined minimalism both work - the key is intentionality, not intensity
- Draw inspiration from the subject's industry, subject matter, materials, and vernacular

### Typography
- Choose fonts that are beautiful, unique, and interesting
- Avoid generic fonts like Arial and Inter
- Opt for distinctive choices that elevate the frontend's aesthetics
- Pair a distinctive display font with a refined body font
- Use one font family or two (if two, make them clearly distinct)
- Avoid accenting just a single word or phrase in headlines
- Avoid using all caps for labels
- Avoid unnecessary typographic labels above content

### Visual Structure
- Treat visual structure as information - outlines, borders, numbering, eyebrows, dividers, labels encode useful information
- Before adding numbered markers, check if the content is actually a sequence
- Use non-user-triggered motion sparingly and deliberately to draw attention
- Consider written content carefully - copy can make a design feel templated

### Process
1. **Plan**: Develop layout concepts using prose descriptions and ASCII wireframes
2. **Review**: Check against the brief and principles
3. **Build**: Implement the design
4. **Critique**: Evaluate and refine

### Layout
- Use one-sentence prose descriptions and ASCII wireframes to ideate and compare
- Include alignment guidance (left, center, justified)

### Principles
- Define high-level guidance for what makes this page unique
- Focus on what makes the design unforgettable
- Consider constraints (technical requirements, framework, performance, accessibility)
- Define differentiation - what makes this UNFORGETTABLE?

## Implementation Guidelines
- Implement real working code with exceptional attention to aesthetic details
- Make creative choices that feel genuinely designed for the context
- Avoid converging on common choices (like Space Grotesk) across generations
- Match implementation complexity to the aesthetic vision
- Maximalist designs may need elaborate code with extensive animations
- Minimalist designs need restraint, precision, and attention to spacing, typography, and subtle details

## Motion and Interaction
- Use animations for effects and micro-interactions
- Prioritize CSS-only solutions for HTML when possible
- Use Motion library for React when available
- Focus on high-impact moments: staggered reveals on page load
- Use scroll-triggering and hover states strategically

## Color and Theme
- Commit to a cohesive aesthetic
- Develop a thoughtful color palette
- Consider theme variations (light/dark) intentionally

## Spatial Composition
- Consider unexpected layouts, asymmetry, overlap, diagonal flow
- Explore grid-breaking elements
- Work with generous negative space OR controlled density intentionally

---
*This skill adapts Anthropic's frontend-design skill for use with Hermes Agent.*
