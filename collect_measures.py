import time

import requests

URL = "https://www.themealdb.com/api/json/v1/1/random.php"
NB_RECIPES = 50

measures = set()                         # créé UNE fois, avant la boucle

for _ in range(NB_RECIPES):
    response = requests.get(URL, timeout=10)
    response.raise_for_status()
    meal = response.json()["meals"][0]

    for i in range(1, 21):
        measure = (meal.get(f"strMeasure{i}") or "").strip()
        if not measure:                  # champ vide, " " ou null : on saute
            continue
        measures.add(measure)

    time.sleep(0.5)                      # ne pas bombarder une API gratuite

with open("measures.txt", "w") as f:
    for measure in sorted(measures):
        f.write(measure + "\n")

print(f"{len(measures)} quantités différentes enregistrées dans measures.txt")