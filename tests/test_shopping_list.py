import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shopping_list import aggregate


def test_same_ingredient_is_summed_case_insensitive():
    totals = aggregate([("Olive Oil", "2 tbsp"), ("olive oil", "1 tbsp")])
    assert totals == {("olive oil", "ml"): 45}


def test_mass_units_are_converted_to_grams():
    totals = aggregate([("Flour", "500g"), ("Flour", "1 kg")])
    assert totals == {("flour", "g"): 1500}


def test_incompatible_units_stay_separate():
    # Un volume et une masse : impossible à additionner sans la densité
    totals = aggregate([("Butter", "2 tbsp"), ("Butter", "200g")])
    assert totals == {("butter", "ml"): 30, ("butter", "g"): 200}


def test_counts_without_unit_are_summed():
    totals = aggregate([("Onion", "1 chopped"), ("Onion", "2")])
    assert totals == {("onion", None): 3}


def test_unmeasurable_ingredient_listed_once_without_quantity():
    totals = aggregate([("Salt", "to taste"), ("Salt", "Pinch")])
    assert totals == {("salt", None): None, ("salt", "pincée"): 1}