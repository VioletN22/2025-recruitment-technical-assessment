from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify
import re

# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
	name: str

@dataclass
class RequiredItem():
	name: str
	quantity: int

@dataclass
class Recipe(CookbookEntry):
	required_items: List[RequiredItem]

@dataclass
class Ingredient(CookbookEntry):
	cook_time: int


# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook = {}

# Task 1 helper (don't touch)
@app.route("/parse", methods=['POST'])
def parse():
	data = request.get_json()
	recipe_name = data.get('input', '')
	parsed_name = parse_handwriting(recipe_name)
	if parsed_name is None:
		return 'Invalid recipe name', 400
	return jsonify({'msg': parsed_name}), 200

# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that 
def parse_handwriting(recipeName: str) -> Union[str | None]:
	correct = recipeName.replace('-', ' ').replace('_', ' ')
	correct = re.sub(r'[^a-zA-Z\s]', '', correct)
	correct = ' '.join(correct.split())
	if not correct:
		return None
	correct = ' '.join(word.capitalize() for word in correct.split())
	
	return correct


# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route('/entry', methods=['POST'])
def create_entry():
	data = request.get_json()
	entry_type = data.get("type")
	name = data.get("name")

	if entry_type not in ["recipe", "ingredient"] or name in cookbook:
		return "Invalid entry", 400

	if entry_type == "ingredient":
		cook_time = data.get("cookTime")
		if cook_time < 0:
			return "Invalid cookTime", 400
		cookbook[name] = Ingredient(name, cook_time)

	elif entry_type == "recipe":
		required_items = data.get("requiredItems", [])
		check = set()
		items = []
		for item in required_items:
			if "name" not in item or "quantity" not in item:
				return "Invalid requiredItem", 400
			if item["name"] in check:
				return "Duplicate requiredItem", 400
			check.add(item["name"])
			items.append(RequiredItem(item["name"], item["quantity"]))

		cookbook[name] = Recipe(name, items)

	return "", 200

# [TASK 3] ====================================================================
# Endpoint that returns a summary of a recipe that corresponds to a query name
#Helper for Task3
def get_ingredients(items):
        total_cook_time = 0
        base_ingredients = {}

        for item in items:
            entry = cookbook.get(item.name)

            if isinstance(entry, Ingredient):
                total_cook_time += entry.cook_time * item.quantity
                base_ingredients[item.name] = base_ingredients.get(item.name, 0) + item.quantity
            elif isinstance(entry, Recipe):
                cook_time, sub_ingredients = get_ingredients(entry.required_items)
                total_cook_time += cook_time
                for ingr, qty in sub_ingredients.items():
                    base_ingredients[ingr] = base_ingredients.get(ingr, 0) + qty

        return total_cook_time, base_ingredients

@app.route('/summary', methods=['GET'])
def summary():
	recipe_name = request.args.get("name")

	if recipe_name not in cookbook or not isinstance(cookbook[recipe_name], Recipe):
		return "", 400

	recipe = cookbook[recipe_name]

	total_cook_time, ingredients = get_ingredients(recipe.required_items)

	return jsonify({
		"name": recipe_name,
		"cookTime": total_cook_time,
		"ingredients": [{"name": k, "quantity": v} for k, v in ingredients.items()]
	})
	


# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
	app.run(debug=True, port=8080)
