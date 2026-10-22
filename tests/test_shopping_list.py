import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shopping_list import aggregate, build_list, round_for_shopping


# ------------------------------------------------ addition (sans traduction)

def test_same_ingredient_is_summed_case_insensitive():
    totals, _ = aggregate([("Olive Oil", "2 tbsp"), ("olive oil", "1 tbsp")])
    assert totals == {("olive oil", "ml"): 45}


def test_mass_units_are_converted_to_grams():
    totals, _ = aggregate([("Flour", "500g"), ("Flour", "1 kg")])
    assert totals == {("flour", "g"): 1500}


def test_incompatible_units_stay_separate():
    # Un volume et une masse : impossible à additionner sans la densité
    totals, _ = aggregate([("Butter", "2 tbsp"), ("Butter", "200g")])
    assert totals == {("butter", "ml"): 30, ("butter", "g"): 200}


def test_counts_without_unit_are_summed():
    totals, _ = aggregate([("Onion", "1 chopped"), ("Onion", "2")])
    assert totals == {("onion", None): 3}


def test_unmeasurable_ingredient_listed_once_without_quantity():
    totals, _ = aggregate([("Salt", "to taste"), ("Salt", "Pinch")])
    assert totals == {("salt", None): None, ("salt", "pincée"): 1}


# ----------------------------------------------------------- traduction

def test_translation_groups_ingredients():
    # Deux noms anglais traduits pareil sont additionnés ensemble
    translations = {"onion": "oignons", "onions": "oignons"}
    totals, untranslated = aggregate([("Onion", "1"), ("Onions", "2")], translations)
    assert totals == {("oignons", None): 3}
    assert untranslated == set()


def test_untranslated_names_are_reported():
    totals, untranslated = aggregate([("Ackee", "1 can")], {})
    assert totals == {("ackee", "boîte"): 1}
    assert untranslated == {"ackee"}


# ------------------------------------------------------------ arrondis

def test_rounding_to_realistic_quantities():
    assert round_for_shopping(453.6, "g") == (500, "g")
    assert round_for_shopping(45, "ml") == (50, "ml")
    assert round_for_shopping(1500, "g") == (1.5, "kg")
    assert round_for_shopping(0.5, None) == (1, None)      # une demi-mangue s'achète entière
    assert round_for_shopping(3, "gousse") == (3, "gousse")


# ------------------------------------------------------- placard

def test_pantry_items_go_to_check_list():
    totals = {("sel", None): None, ("huile d'olive", "ml"): 45, ("poulet", "g"): 450}
    to_buy, to_check = build_list(totals, pantry={"sel", "huile d'olive"})
    assert to_buy == [("poulet", 450, "g")]
    assert to_check == ["huile d'olive", "sel"]


def test_no_duplicate_line_without_quantity():
    # « to taste » + « 2 » pour le même ingrédient : une seule ligne, avec la quantité
    totals = {("coriandre", None): None, ("coriandre", "botte"): 1}
    to_buy, _ = build_list(totals, pantry=set())
    assert to_buy == [("coriandre", 1, "botte")]