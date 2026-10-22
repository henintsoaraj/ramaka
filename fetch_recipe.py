import requests

URL = "https://www.themealdb.com/api/json/v1/1/random.php"

response = requests.get(URL, timeout=10)
response.raise_for_status()          # erreur si la réponse n'est pas un succès (200)
meal = response.json()["meals"][0]

print(meal["strMeal"], "-", meal.get("strArea") or "origine inconnue")

ingredients = []
for i in range(1, 21):
    name = meal.get(f"strIngredient{i}")
    measure = meal.get(f"strMeasure{i}")
    if not name or not name.strip():     # champ vide, " " ou null : on saute
        continue
    ingredients.append((name.strip(), (measure or "").strip()))

for name, measure in ingredients:
    print(f"- {name} : {measure}")