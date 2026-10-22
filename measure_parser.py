import difflib
import re
from collections import Counter

# Unités reconnues : variantes anglaises -> unité française normalisée
UNITS = {
    "g": "g", "gr": "g", "gram": "g", "grams": "g",
    "kg": "kg",
    "ml": "ml", "l": "l", "litre": "l", "liter": "l",
    "tsp": "c. à café", "teaspoon": "c. à café", "teaspoons": "c. à café",
    "tbsp": "c. à soupe", "tbs": "c. à soupe", "tablespoon": "c. à soupe",
    "tablespoons": "c. à soupe",
    "cup": "tasse", "cups": "tasse",
    "oz": "oz", "lb": "livre", "lbs": "livre",
    "pinch": "pincée", "pinches": "pincée",
    "clove": "gousse", "cloves": "gousse",
    "can": "boîte", "cans": "boîte", "tin": "boîte", "tins": "boîte",
    # Ajouts de la version 2 (repérés dans l'échantillon)
    "sprig": "brin", "sprigs": "brin",
    "slice": "tranche", "slices": "tranche",
    "packet": "sachet", "packets": "sachet",
    "handful": "poignée", "handfuls": "poignée",
    "bunch": "botte", "bunches": "botte",
    "knob": "noix",
    "dash": "trait", "splash": "trait",
    # Ajouts de la version 3 (repérés dans le second échantillon)
    "head": "tête", "heads": "tête",
    "pot": "pot", "pots": "pot",
    "scoop": "boule", "scoops": "boule",
    "pod": "gousse", "pods": "gousse",
    "jar": "bocal", "jars": "bocal",
    "pound": "livre", "pounds": "livre",
}

# Fractions écrites en un seul caractère
UNICODE_FRACTIONS = {"½": "1/2", "¼": "1/4", "¾": "3/4", "⅓": "1/3", "⅔": "2/3"}


def find_unit(word):
    """Unité normalisée d'un mot, en tolérant les fautes de frappe ; None sinon."""
    w = word.lower().strip(".")
    if w in UNITS:
        return UNITS[w]
    # Pas de tolérance sur les mots courts, ni sur les préparations en -ed
    # ("sliced" ressemble à 91 % à "slice", mais c'est une préparation, pas une unité)
    if len(w) >= 4 and not w.endswith("ed"):
        close = difflib.get_close_matches(w, UNITS.keys(), n=1, cutoff=0.85)
        if close:
            return UNITS[close[0]]
    return None

# Nombres écrits en lettres
NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "half": 0.5}

# Un nombre : "1 1/2" (mixte), "1/2" (fraction), "2", "0.5" ou "0,5" (décimal)
NUMBER = r"(\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)"

# Règle 1 : un nombre AU DÉBUT, puis éventuellement un mot (collé ou non), puis le reste
AT_START = re.compile(rf"^\s*{NUMBER}\s*([a-zA-Z]+)?\.?\s*(.*)$")

# Règle 2 : un nombre (en chiffres ou en lettres) À LA FIN
AT_END = re.compile(
    rf"^(.*?)\s*(?:{NUMBER}|\b({'|'.join(NUMBER_WORDS)})\b)\s*$",
    re.IGNORECASE,
)


def to_float(text):
    """'1 1/2' -> 1.5, '1/2' -> 0.5, '0,5' -> 0.5, '2' -> 2.0"""
    total = 0.0
    for part in text.split():
        if "/" in part:
            num, den = part.split("/")
            total += int(num) / int(den)
        else:
            total += float(part.replace(",", "."))
    return total


def parse_measure(text):
    """Renvoie (quantité, unité, note). quantité et unité peuvent valoir None."""
    text = text.strip()

    # Préparation : fractions en un caractère ("½" -> "1/2", "1½" -> "1 1/2")
    for char, fraction in UNICODE_FRACTIONS.items():
        text = re.sub(rf"(\d)\s*{char}", rf"\1 {fraction}", text)
        text = text.replace(char, fraction)

    # Préparation : une précision entre parenthèses rejoint la note ("1 (12 oz.)")
    extra = " ".join(re.findall(r"\(.*?\)", text))
    if extra:
        text = re.sub(r"\(.*?\)", " ", text).strip()
        quantity, unit, note = parse_measure(text)
        return quantity, unit, f"{note} {extra}".strip()

    # Règle 1 : nombre au début ("2 tbsp", "200g", "1 chopped")
    match = AT_START.match(text)
    if match:
        number, word, rest = match.groups()
        quantity = to_float(number)
        unit = find_unit(word) if word else None
        if unit:
            return quantity, unit, rest.strip()
        # Le mot n'est pas une unité connue ("1 chopped") : il rejoint la note
        return quantity, None, f"{word or ''} {rest}".strip()

    # Règle 2 : nombre à la fin, en chiffres ou en lettres ("Juice of 1", "zest of one")
    match = AT_END.match(text)
    if match:
        before, digits, word_number = match.groups()
        quantity = to_float(digits) if digits else float(NUMBER_WORDS[word_number.lower()])
        return quantity, None, before.strip()

    # Règle 3 : une unité sans nombre ("Pinch", "Large handful") : 1 sous-entendu
    words = text.split()
    for i, w in enumerate(words):
        unit = find_unit(w)
        if unit:
            note = " ".join(words[:i] + words[i + 1:])
            return 1.0, unit, note

    # Règle 4 : vraiment du texte ("To taste") : une note, rien à additionner
    return None, None, text


if __name__ == "__main__":
    with open("measures.txt") as f:
        measures = [line.strip() for line in f if line.strip()]

    families = Counter()
    examples = {"nombre seul": [], "texte seul": []}
    for m in measures:
        quantity, unit, note = parse_measure(m)
        if quantity is not None and unit is not None:
            families["nombre + unité"] += 1
        elif quantity is not None:
            families["nombre seul"] += 1
            examples["nombre seul"].append(m)
        else:
            families["texte seul"] += 1
            examples["texte seul"].append(m)

    total = len(measures)
    print(f"{total} quantités analysées\n")
    for family, count in families.most_common():
        print(f"{family:15} {count:4}  ({100 * count / total:.0f} %)")

    for family, items in examples.items():
        print(f"\nExemples de « {family} » :")
        for m in items[:20]:
            print(" ", m)