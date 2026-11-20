#!/usr/bin/env python3
"""Find recipes from ingredients using Claude Haiku."""

import os, sys, json
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "10"))
MAX_TOKENS_PER_RUN = int(os.environ.get("MAX_TOKENS_PER_RUN", "50000"))

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("Error: ANTHROPIC_API_KEY not found in .env file.")
    sys.exit(1)

client = Anthropic(api_key=api_key)
FAV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favorites.json")

HELP = """Recipe Finder — AI Personal Chef
Usage:
  python recipe_finder.py ing1, ing2, ing3
  python recipe_finder.py --favorites
  python recipe_finder.py --help"""


def load_favs() -> dict:
    if os.path.exists(FAV_FILE):
        with open(FAV_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_fav(name: str, ings: list[str], details: str) -> None:
    favs = load_favs()
    favs[name.lower().replace(" ", "_")] = {
        "name": name, "ingredients": ings, "details": details,
        "saved_at": datetime.now().isoformat(),
    }
    with open(FAV_FILE, "w", encoding="utf-8") as f:
        json.dump(favs, f, indent=2)
    print(f"Saved '{name}' to favorites!")


def show_favs() -> None:
    favs = load_favs()
    if not favs:
        print("No favorites yet!")
        return
    print(f"\nYour Favorites ({len(favs)}):")
    for k, r in favs.items():
        print(f"  {r['name']} [{', '.join(r['ingredients'])}]")


def parse_ingredients() -> list[str]:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(HELP)
        sys.exit(1)
    raw = " ".join(args)
    return [i.strip().lower() for i in raw.split(",") if i.strip()]


def suggest_recipes(ings: list[str]) -> str:
    resp = client.messages.create(
        model="claude-haiku-5-5", max_tokens=1000,
        system="You are a professional chef.",
        messages=[{"role": "user",
                    "content": f"Ingredients:\n" + "\n".join(f"- {i}" for i in ings) + "\nSuggest 3 recipes with match %, extras needed, time, difficulty."}],
    )
    return resp.content[0].text


def get_details(name: str, ings: list[str]) -> str:
    resp = client.messages.create(
        model="claude-haiku-5-5", max_tokens=1500,
        system="You are a professional chef.",
        messages=[{"role": "user",
                    "content": f'Make "{name}" with: {", ".join(ings)}\nGive quantities and numbered steps.'}],
    )
    return resp.content[0].text


def main() -> None:
    if "--favorites" in sys.argv:
        show_favs()
        return
    if "--help" in sys.argv or "-h" in sys.argv:
        print(HELP)
        return

    ings = parse_ingredients()
    print(f"\nIngredients: {', '.join(ings)}")
    print("Asking Claude for recipe suggestions...\n")

    suggestions = suggest_recipes(ings)
    print(suggestions)
    print("\n" + "=" * 50)

    choice = input("\nEnter 1-3 for details, 'save N' to save, Enter to exit: ").strip().lower()

    if choice.startswith("save "):
        num = choice.split()[-1]
        for line in suggestions.split("\n"):
            if line.startswith(f"{num}."):
                name = line.split(".", 1)[1].strip().split("(")[0].strip()
                save_fav(name, ings, suggestions)
                break
        return

    if choice in ("1", "2", "3"):
        name = ""
        for line in suggestions.split("\n"):
            if line.startswith(f"{choice}."):
                name = line.split(".", 1)[1].strip().split("(")[0].strip()
                break
        print(f"\n--- {name or 'Recipe ' + choice} ---\n")
        details = get_details(name or f"Recipe {choice}", ings)
        print(details)
        if input(f"\nSave '{name or 'Recipe ' + choice}'? (y/n): ").strip().lower() == "y":
            save_fav(name or f"Recipe {choice}", ings, details)
    elif choice == "":
        print("Happy cooking!")
    else:
        print(f"Unknown: '{choice}'. Run again with ingredients.")


if __name__ == "__main__":
    main()
