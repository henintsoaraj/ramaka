import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from measure_parser import parse_measure

# Jeu de référence : (texte tel que fourni par TheMealDB, résultat attendu)
# Résultat attendu = (quantité, unité normalisée, note)
REFERENCE = [
    # --- Nombre + unité
    ("2 tbsp", (2.0, "c. à soupe", "")),
    ("200g", (200.0, "g", "")),
    ("1 1/2 cups", (1.5, "tasse", "")),
    ("0,5 l", (0.5, "l", "")),
    ("2 cloves chopped", (2.0, "gousse", "chopped")),
    ("3 sprigs", (3.0, "brin", "")),
    ("4 slices", (4.0, "tranche", "")),
    ("1 packet", (1.0, "sachet", "")),
    # --- Nombre seul (l'unité est l'ingrédient lui-même : « 1 oignon »)
    ("1/2", (0.5, None, "")),
    ("1 chopped", (1.0, None, "chopped")),
    ("3 large", (3.0, None, "large")),
    # --- Unité sans nombre : le nombre 1 est sous-entendu
    ("Pinch", (1.0, "pincée", "")),
    ("Handful", (1.0, "poignée", "")),
    ("Large handful", (1.0, "poignée", "Large")),
    ("Knob", (1.0, "noix", "")),
    # --- Nombre à la fin, ou écrit en lettres
    ("Juice of 1", (1.0, None, "Juice of")),
    ("Grated Zest of 2", (2.0, None, "Grated Zest of")),
    ("The juice and zest of one", (1.0, None, "The juice and zest of")),
    # --- Vraiment du texte : rien à additionner
    ("To taste", (None, None, "To taste")),
    ("To serve", (None, None, "To serve")),
]


@pytest.mark.parametrize("text, expected", REFERENCE)
def test_parse_measure(text, expected):
    assert parse_measure(text) == expected