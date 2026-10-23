from fastapi import Query, FastAPI
from shopping_list import fetch_recipe, aggregate, build_list, load_json

TRANSLATIONS = load_json("ingredients_fr.json")
PANTRY = set(load_json("placard.json"))

app = FastAPI()

@app.get("/sante")
def sante():
    return {"statut": "ok"}

@app.get("/liste-de-courses")
def liste_de_courses(recette: list[str] = Query()):
    all_ingredients = []
    for name in recette:
        title, ingredients = fetch_recipe(name)
        all_ingredients.extend(ingredients)

    totals, untranslated = aggregate(all_ingredients, TRANSLATIONS)
    to_buy, to_check = build_list(totals, PANTRY)

    return {
        "a_acheter": [{"nom": n, "quantite": q, "unite": u} for n, q, u in to_buy],
        "a_verifier": to_check,
        "non_traduits": sorted(untranslated),
    }