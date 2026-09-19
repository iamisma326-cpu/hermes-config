---
name: component-registry-development
description: Use when adding/editing components in components-catalog.
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [frontend, react, shadcn, registry, accessibility]
    related_skills: [plan, component-thumbnail, writing-tests]
---

# Component Registry Development

## When to Use

- Adding, editing, or auditing components in `~/projects/components` (components-catalog).
- Researching whether a component idea is unique before building it.
- Extending the catalog with a new family/category or wiring registry endpoints.

Class: building and maintaining a copy-paste component registry (shadcn-style) with its own installable `/r/<slug>.json` endpoints, a catalog site, and quality gates. Verified against `~/projects/components` (components-catalog: Next 16 + React 19 + Tailwind 4 + Turborepo).