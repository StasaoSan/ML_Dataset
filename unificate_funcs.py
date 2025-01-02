import numpy as np
import re
from conversation_dict import unit_conversion, fraction_conversion


def time_to_minutes(time):
    hours = 0
    minutes = 0

    hours_match = re.search(r'(\d+)\s*hr', time)
    if hours_match:
        hours = int(hours_match.group(1))

    minutes_match = re.search(r'(\d+)\s*min', time)
    if minutes_match:
        minutes = int(minutes_match.group(1))

    total_minutes = hours * 60 + minutes
    return total_minutes


def process_servings(servings_value):
    if isinstance(servings_value, str) and 'to' in servings_value:
        parts = servings_value.split('to')
        try:
            return str((float(parts[0].strip()) + float(parts[1].strip())) / 2)
        except ValueError:
            return np.nan

    if isinstance(servings_value, str):
        try:
            return str(float(servings_value.split()[0]))
        except (ValueError, IndexError):
            return np.nan

    return servings_value


# //////////
def handle_fractional_numbers(ingredient):
    for frac, dec in fraction_conversion.items():
        ingredient = ingredient.replace(frac, str(dec))

    ingredient = re.sub(r'(\d+)\s+(\d+\.\d+)', lambda match: str(float(match.group(1)) + float(match.group(2))),
                        ingredient)

    return ingredient


def convert_to_base_unit(quantity, unit):
    unit = unit.lower()
    if unit in unit_conversion:
        return quantity * unit_conversion[unit], unit_conversion[unit]
    return quantity, None


def unificate_ingr(ingredient):
    ingredient = handle_fractional_numbers(ingredient)

    match = re.search(r'(\d+(\.\d+)?)\s*([a-zA-Z]+)', ingredient)

    if match:
        quantity = float(match.group(1))
        unit = match.group(3)

        converted_quantity, conversion_factor = convert_to_base_unit(quantity, unit)

        if conversion_factor:
            normalized_str = re.sub(r'(\d+(\.\d+)?)\s*([a-zA-Z]+)', f'{converted_quantity:.2f} grams', ingredient)
            return normalized_str

    return ingredient


def unificate_ingredients(ingredients_string):
    if not isinstance(ingredients_string, str):
        return ""
    ingredients = ingredients_string.split(', ')
    ingredients_unificated = [unificate_ingr(ingr) for ingr in ingredients]
    return ', '.join(ingredients_unificated)
