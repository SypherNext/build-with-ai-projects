# Build with AI -- Reference Implementations

Reference implementations for the projects in Sypher's `build-with-ai`
course. Each project is a finished, verified version of what its lesson
teaches you to build step by step -- type the lesson yourself first; come
here to compare your output, see it run, or get unstuck.

Unlike a companion app you build INTO across a whole course (see the
`python-for-ai-engineers` track's `doc-scout`), every project here is
independent: no shared state, no step-by-step scaffolding needed, since
each lesson already walks through the full build with complete code.

## Layout

```
mini-projects/          Single-file CLI scripts (10 projects)
intermediate-projects/   Added when that tier is scoped
production-projects/     Added when that tier is scoped
portfolio-projects/      Added when that tier is scoped
```

Each project folder is self-contained: its own `requirements.txt`,
`.env.example`, and `README.md` with setup/run instructions. None of them
depend on another project in this repo.

## Setup

All current (Mini) projects are Python 3.10+ and call the Anthropic API
(Claude Haiku). Per-project setup:

```bash
cd mini-projects/<project-name>
python -m venv venv
source venv/bin/activate   # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env       # add your ANTHROPIC_API_KEY (console.anthropic.com)
```

A few projects need an extra API key (noted in their own README) or are
meant to run on a schedule via cron / Task Scheduler.

## License

Copyright (C) 2026 SypherNext

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). You may
use, study and change it. If you share a modified version, or run one as a website or service
that other people use, you must make your full modified source code available under the same
license. See [LICENSE](LICENSE) for the full terms.
