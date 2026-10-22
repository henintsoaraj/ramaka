import json
import math
import sys
import time
from pathlib import Path

import requests

from measure_parser import parse_measure

SEARCH_URL = "https://www.themealdb.com/api/json/v1/1/search.php"
HERE = Path(__file__).parent

# Conversion vers une unité de base, par famille d'unités
TO_GRAMS = {"g": 1, "kg": 1000, "livre": 453.6, "oz": 28.35}
TO_ML = {"ml": 1, "l": 1000, "tasse": 240, "c. à soupe": 15, "c. à café": 5}


def load_json(filename):
    with open(HERE / filename, encoding="utf-8") as f:
        return json.load(f)


def to_base(quantity, unit):
    """Convertit vers g ou ml si possible ; sinon garde l'unité telle quelle."""
    if unit in TO_GRAMS:
        return quantity * TO_GRAMS[unit], "g"
    if unit in TO_ML:
        return quantity * TO_ML[unit], "ml"
    return quantity, unit


def fetch_recipe(name):
    """Cherche une recette par son nom ; renvoie (titre, [(ingrédient, quantité)])."""
    response = requests.get(SEARCH_URL, params={"s": name}, timeout=10)
    response.raise_for_status()
    meals = response.json().get("meals")
    if not meals:
        raise ValueError(f"Aucune recette trouvée pour « {name} »")
    meal = meals[0]

    ingredients = []
    for i in range(1, 21):
        ingredient = (meal.get(f"strIngredient{i}") or "").strip()
        if not ingredient:
            continue
        ingredients.append((ingredient, (meal.get(f"strMeasure{i}") or "").strip()))
    return meal["strMeal"], ingredients


def aggregate(ingredients, translations=None):
    """Additionne une liste de (ingrédient, quantité en texte).

    Si `translations` est fourni, les noms sont traduits AVANT l'addition :
    deux ingrédients anglais traduits pareil sont donc regroupés.
    Renvoie ({(nom, unité): quantité totale ou None}, {noms non traduits})."""
    totals = {}
    untranslated = set()
    for ingredient, measure in ingredients:
        quantity, unit, _note = parse_measure(measure)
        name = ingredient.lower()
        if translations is not None:
            if name in translations:
                name = translations[name]
            else:
                untranslated.add(name)

        if quantity is None:
            totals.setdefault((name, None), None)     # à avoir, sans quantité
            continue

        quantity, unit = to_base(quantity, unit)
        key = (name, unit)
        totals[key] = (totals.get(key) or 0) + quantity
    return totals, untranslated


def round_for_shopping(quantity, unit):
    """Arrondit à une quantité réaliste pour faire ses courses."""
    if unit in ("g", "ml"):
        step = 10 if quantity < 100 else 50 if quantity < 1000 else 100
        quantity = max(step, math.ceil(quantity / step) * step)
        if quantity >= 1000:
            return quantity / 1000, "kg" if unit == "g" else "l"
        return quantity, unit
    # Pièces, bottes, gousses... : on n'achète pas une demi-botte
    return math.ceil(quantity), unit


def build_list(totals, pantry):
    """Sépare ce qu'il faut acheter de ce qu'il faut vérifier dans le placard."""
    to_buy, to_check = [], set()
    for (name, unit), quantity in totals.items():
        if name in pantry:
            to_check.add(name)
        elif quantity is None:
            to_buy.append((name, None, None))
        else:
            q, u = round_for_shopping(quantity, unit)
            to_buy.append((name, q, u))

    # Un ingrédient listé avec une quantité n'a pas besoin d'une ligne sans quantité
    measured = {name for name, q, _ in to_buy if q is not None}
    to_buy = [item for item in to_buy if item[1] is not None or item[0] not in measured]
    return sorted(to_buy), sorted(to_check)


def format_line(name, quantity, unit):
    if quantity is None:
        return f"- {name}"
    if quantity == int(quantity):
        quantity = int(quantity)
    else:
        quantity = str(round(quantity, 1)).replace(".", ",")
    return f"- {name} : {quantity} {unit or ''}".rstrip()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage : python shopping_list.py "Recette 1" "Recette 2" ...')
        sys.exit(1)

    translations = load_json("ingredients_fr.json")
    pantry = set(load_json("placard.json"))

    all_ingredients = []
    for recipe_name in sys.argv[1:]:
        title, ingredients = fetch_recipe(recipe_name)
        print(f"Recette : {title} ({len(ingredients)} ingrédients)")
        all_ingredients.extend(ingredients)
        time.sleep(0.5)

    totals, untranslated = aggregate(all_ingredients, translations)
    to_buy, to_check = build_list(totals, pantry)

    print("\nÀ ACHETER")
    for name, quantity, unit in to_buy:
        print(format_line(name, quantity, unit))

    print("\nÀ VÉRIFIER DANS LE PLACARD")
    for name in to_check:
        print(f"- {name}")

    if untranslated:
        print("\n(Non traduits, à ajouter à ingredients_fr.json : "
              + ", ".join(sorted(untranslated)) + ")")