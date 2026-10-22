import sys
import time

import requests

from measure_parser import parse_measure

SEARCH_URL = "https://www.themealdb.com/api/json/v1/1/search.php"

# Conversion vers une unité de base, par famille d'unités
TO_GRAMS = {"g": 1, "kg": 1000, "livre": 453.6, "oz": 28.35}
TO_ML = {"ml": 1, "l": 1000, "tasse": 240, "c. à soupe": 15, "c. à café": 5}


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


def aggregate(ingredients):
    """Additionne une liste de (ingrédient, quantité en texte).

    Renvoie un dict {(ingrédient, unité): quantité totale}, où la quantité
    vaut None quand rien n'est mesurable (« to taste »)."""
    totals = {}
    for ingredient, measure in ingredients:
        quantity, unit, _note = parse_measure(measure)
        name = ingredient.lower()

        if quantity is None:
            totals.setdefault((name, None), None)     # à avoir, sans quantité
            continue

        quantity, unit = to_base(quantity, unit)
        key = (name, unit)
        totals[key] = (totals.get(key) or 0) + quantity
    return totals


def format_line(name, unit, quantity):
    if quantity is None:
        return f"- {name}"
    quantity = round(quantity, 1)
    if quantity == int(quantity):
        quantity = int(quantity)
    return f"- {name} : {quantity} {unit or ''}".rstrip()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage : python shopping_list.py "Recette 1" "Recette 2" ...')
        sys.exit(1)

    all_ingredients = []
    for recipe_name in sys.argv[1:]:
        title, ingredients = fetch_recipe(recipe_name)
        print(f"Recette : {title} ({len(ingredients)} ingrédients)")
        all_ingredients.extend(ingredients)
        time.sleep(0.5)

    totals = aggregate(all_ingredients)
    print(f"\nListe de courses ({len(totals)} lignes) :")
    for (name, unit), quantity in sorted(totals.items(), key=lambda kv: kv[0][0]):
        print(format_line(name, unit, quantity))