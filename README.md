# AI Translation for Everyday Life

**A manual for multilingual households who use AI to understand daily
paperwork: school notices, medical and rental documents, utility letters,
and government forms.**

Written by [Dylan Asdale](https://dylanasdale.github.io) and published by
**Asdale Dynamics, LLC** — plain English, step by step, never condescending.

The manual teaches one repeatable workflow: read a document's structure
before translating anything, keep personal details out of cloud tools,
verify the AI's draft before you act on it, and know when the right move is
a human office instead of a fresh translation. It is deliberately *not* a
language-learning guide — no vocabulary drills, no conjugations. This is
about today's paperwork, not studying grammar.

## What's inside

- **`docs/`** — the manual in Markdown: 10 numbered chapters (welcome,
  structure-first reading, everyday documents, medical paperwork, rental,
  government forms, privacy, verification, human offices, hard lines) plus
  a one-page **Verification Checklist** and a plain-English **Glossary**.
- **`script/build.py`** — builds the whole manual into a static HTML site
  (`site/`). Pure Python standard library: no network, no dependencies, no
  JavaScript on any page.
- **`test/`** — pytest suite guarding the content (all hard lines present,
  checklist is actionable, glossary complete, no secrets or personal data)
  and the build (every page well-formed, all links resolve, rebuilds are
  fresh).

## Run it

```sh
# build the static site (Python 3.10+)
python3 script/build.py          # -> site/index.html

# run the tests
python3 -m pytest test/

# both, or rebuild without typing commands
make build
make test
```

The `site/` folder is plain HTML: open `site/index.html` in any browser,
put it on a phone, or print any page. Nothing phones home — the manual
practices its own privacy advice.

## The rules of this manual, in one breath

1. **Read the structure first.** Who sent it, what type it is, what's due,
   by when, what happens if you miss it.
2. **Strip personal details before any cloud AI sees the document.**
   Names, IDs, addresses, account numbers (Chapter 6's red list).
3. **Verify before you act.** Anchor terms, second tool, back-translation,
   human spot-check (Chapter 7's layers, Chapter 10's checklist).
4. **AI never signs anything.** No signed legal or medical decisions, ever.
   That's a human's job — often the office on the letter (Chapter 8).
5. **In an emergency: call, don't translate.**

## Where this project's line is (and is not)

This is education only. It is not legal, medical, or immigration advice,
and it is not a certified translation service. If a document carries real
consequences — a signature, a diagnosis, a court date, a deadline — this
manual will keep pointing you at a human professional. That's the point,
not a bug.

## How this is different from the language-learning guide

Asdale Dynamics also publishes a separate guide about *learning* languages
with AI (study plans, practice partners, spaced repetition). That's a
different project with a different goal. This manual is for households who
need to **understand specific documents today** — a bill due Friday, a
rent-increase notice, a school form — and need to do it safely,
repeatedly, without becoming language students along the way.

## About the series

Part of the Asdale Dynamics beginner AI manual series — practical,
privacy-respecting guides that explain AI like a friend would.
Project status and known gaps live in **STATUS.md**.

## License

MIT — see [LICENSE](LICENSE).
Copyright (c) 2026 Asdale Dynamics, LLC.
