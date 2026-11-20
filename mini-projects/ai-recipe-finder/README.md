# AI Recipe Finder

Reference implementation for the "AI Recipe Finder" Mini Project in Sypher's
`build-with-ai` course. A Python CLI where you list the ingredients you have
and Claude Haiku suggests three recipes ranked by match percentage, with
step-by-step instructions and a local JSON favorites list.

This is the finished, verified version -- type the lesson's own steps
yourself first; come back here to compare your output or see it run.

## Setup

```bash
python -m venv venv
source venv/bin/activate   # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env       # then add your ANTHROPIC_API_KEY
```

## Run

```bash
python recipe_finder.py tofu, kale, bell pepper, eggs, soy sauce
python recipe_finder.py --favorites
python recipe_finder.py --help
```
