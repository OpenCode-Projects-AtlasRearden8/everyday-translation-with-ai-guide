# STATUS.md

Last updated: 2026-11-05

## What was built

**AI Translation for Everyday Life** — a complete beginner manual for
multilingual households using AI to understand daily paperwork, plus the
local-first tooling to read it and test it.

- **Manual (`docs/`, 12 Markdown files):**
  - `00-introduction.md` — who it's for, what AI is/isn't for here, and an
    explicit disclaimer that this is *not* a language-learning guide.
  - `01` reading a document's structure before translating (six-part
    skeleton + a copyable structure-reading prompt).
  - `02` everyday documents: school notices and utility letters, with
    ready-to-use prompts.
  - `03` medical paperwork: understand-only rules, interpreter rights,
    "ledger terms anchored in both languages" workflow.
  - `04` rental/housing: stakes ladder, lease-in-slices method.
  - `05` government forms: field-by-field translation, statement rules,
    human-confirmation-first deadline handling, office-visit card.
  - `06` privacy first: red list of personal details, placeholder scheme,
    local/offline options, Two-Question Test. Keeps personal data out of
    cloud tools.
  - `07` verifying a translation: four layers (sense check, anchor terms,
    back-translation, human spot-check).
  - `08` what to ask a human office instead: who to ask for what, call
    script, interpreter-request phrase.
  - `09` hard lines: never for anything signed, never for medical
    decisions, never composing official statements, never in emergencies.
  - `10` verification checklist: printable, checkbox-styled, 30-second
    collapse for low stakes.
  - `11` glossary: plain-English definitions, friend-tone.
- **Static site (`script/build.py` → `site/`):** one `index.html` plus one
  page per chapter, table of contents, prev/next pager, warm style, no
  JavaScript, no tracking, no external requests, works offline. Pure
  Python 3 standard library.
- **Tests (`test/`, 32 tests):** build correctness (page count, complete
  HTML, internal links resolve, rebuild wipe) and content guardrails
  (hard-line phrases exist, checklist actionable, glossary terms present,
  cross-references resolve, no secrets/personal data, no external URLs).
- **Housekeeping:** `README.md` (with Asdale Dynamics, LLC credit),
  `LICENSE` (MIT, "Copyright (c) 2026 Asdale Dynamics, LLC"), `Makefile`.

## How to run it

```sh
python3 script/build.py     # builds HTML site into site/ (default)
python3 -m pytest test/     # runs all 32 tests
make build && make test     # same via make
```

Open `site/index.html` in a browser. Nothing needs a network.

## Verification results (2026-11-05)

- `python3 script/build.py` → "Built 13 HTML pages into .../site" — pass.
- `python3 -m pytest test/` → **32 passed** in ~0.1 s — pass.
- Manual spot-checks: TOC/pager links all resolve; checklist page renders
  17 checkbox items; tables, blockquotes, checkboxes, nested bold/italic
  all render correctly; no page contains JavaScript or external links;
  footer carries the Asdale Dynamics, LLC copyright on every page.
- LICENSE copyright line verified character-for-character:
  `Copyright (c) 2026 Asdale Dynamics, LLC`.
- README credits Asdale Dynamics, LLC and separates this project from the
  language-learning guide.

## Known gaps

- **The Markdown renderer is a subset.** It covers everything used in
  `docs/` (headings, lists, checkboxes, blockquotes, tables, inline
  emphasis/code/links, rules). It does not cover arbitrary Markdown
  (nested lists at depth > 1, fenced code blocks, footnotes,
  multi-line table cells). Adding a chapter with heavier formatting may
  tease out edge cases, but tests guard current content.
- **Prompt templates are language-generative, not certified.** The manual
  is careful about this — AI is the first pass, everything with stakes
  goes through verification layers and/or a human — but there is no
  built-in tooling (e.g., no script that automates the back-translation
  round trip). Possible follow-up: a tiny local helper script.
- **Local-AI setup guide is a paragraph, not a chapter.** Chapter 6
  names the option and when to use it; a walkthrough of installing a
  specific offline model on low-end machines is a separate how-to that
  would depend on the reader's hardware.
- **Hero/landing polish.** The site is intentionally minimal and
  print-friendly; no images, dark mode, or search.
- **Only English-language content.** Translations of the manual itself
  (into Spanish, Tagalog, Ukrainian, etc.) are a natural future addition
  and are deliberately out of scope for this commit.
