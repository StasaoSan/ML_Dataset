import re
from difflib import SequenceMatcher
import pandas as pd
import arff
from sklearn.preprocessing import MinMaxScaler

def simplify_ingredients(ingredients):
    simplified_ingredients = []
    for ingredient in ingredients:
        simplified = re.sub(r'\d+\s*\w*', '', ingredient).strip()
        simplified = re.sub(r'[().\/®%-]', '', simplified).strip()
        simplified_ingredients.append(simplified)
    return simplified_ingredients

def find_similar_ingredients(ingredients, threshold=0.75):
    similar_map = {}
    for i in range(len(ingredients)):
        for j in range(i + 1, len(ingredients)):
            if SequenceMatcher(None, ingredients[i], ingredients[j]).ratio() > threshold:
                if len(ingredients[i]) < len(ingredients[j]):
                    similar_map[ingredients[j]] = ingredients[i]
                else:
                    similar_map[ingredients[i]] = ingredients[j]
    return similar_map

def merge_similar_ingredients(ingredient_list, similar_map):
    return [similar_map.get(ingredient, ingredient) for ingredient in ingredient_list]

def normalize_columns(df, columns):
    scaler = MinMaxScaler()
    df[columns] = scaler.fit_transform(df[columns])
    return df

def group_rare_ingredients(ingredients_df, min_frequency=5):
    ingredient_counts = ingredients_df.sum(axis=0)
    rare_ingredients = ingredient_counts[ingredient_counts < min_frequency].index

    ingredients_df['other_ingredients'] = ingredients_df[rare_ingredients].sum(axis=1)
    ingredients_df = ingredients_df.drop(columns=rare_ingredients)

    return ingredients_df

def binarize_data(arff_filename, output_csv):
    with open(arff_filename, 'r') as f:
        dataset = arff.load(f)

    df = pd.DataFrame(dataset['data'], columns=[attr[0] for attr in dataset['attributes']])

    for col in df.select_dtypes(include=[object]).columns:
        if isinstance(df[col].iloc[0], bytes):
            df[col] = df[col].astype(str)
    df.fillna(df.mean(numeric_only=True), inplace=True)

    numeric_columns = df.select_dtypes(include=[float, int]).columns
    df[numeric_columns] = df[numeric_columns].round(1)

    if 'Ingredients' in df.columns:
        df['Ingredients'] = df['Ingredients'].apply(lambda x: simplify_ingredients(x.split(',')) if pd.notna(x) else [])

        unique_ingredients = set([ingredient for sublist in df['Ingredients'] for ingredient in sublist])
        similar_ingredients_map = find_similar_ingredients(list(unique_ingredients))

        df['Ingredients'] = df['Ingredients'].apply(lambda x: merge_similar_ingredients(x, similar_ingredients_map))

        ingredients_df = df['Ingredients'].str.join('|').str.get_dummies()
        ingredients_df = group_rare_ingredients(ingredients_df)

        df = pd.concat([df, ingredients_df], axis=1)
        df = df.drop('Ingredients', axis=1)

    df = df.drop(['URL', 'Title', 'Image_Paths'], axis=1)

    columns_to_normalize = ['Rating', 'Prep_Time_(min)', 'Cook_Time_(min)', 'Total_Time_(min)', 'Servings']
    df = normalize_columns(df, columns_to_normalize)

    if 'Category' in df.columns:
        df['Category'] = df['Category']

    if 'Title' in df.columns:
        df['Title'] = df['Title']

    df.to_csv(output_csv, index=False)

    print(f"Бинаризация завершена. Данные сохранены в {output_csv}. Количество признаков: {len(df.columns)}")
