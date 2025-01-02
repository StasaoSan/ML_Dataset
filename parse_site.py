import os
import requests
import numpy as np
import pandas as pd

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from binarize_data import binarize_data
from arff_helper import write_arff, read_tsv
from unificate_funcs import time_to_minutes, unificate_ingredients, process_servings


def start_parse(tsv_filename, arff_filename, output_csv, filter_keyword=None):
    category_links = get_category_links(filter_keyword)
    all_recipes = []
    for category_url in category_links:
        print(f"Парсинг категории: {category_url}")
        category_recipes = get_recipes_from_category_or_list(category_url)
        all_recipes.extend(category_recipes)
        print(f"Собрано {len(category_recipes)} рецептов из категории {category_url}")

    print(f"Всего рецептов собрано: {len(all_recipes)}")

    df = pd.DataFrame(all_recipes,
                      columns=['URL', 'Title', 'Category', 'Rating', 'Prep_Time_(min)',
                               'Cook_Time_(min)', 'Total_Time_(min)', 'Servings',
                               'Ingredients', 'Image_Paths'])
    df.to_csv(tsv_filename, sep='\t', index=False)

    df = read_tsv(tsv_filename)
    write_arff(df, arff_filename)

    binarize_data(arff_filename, output_csv)


def get_category_links(filter_keyword):
    url = "https://www.allrecipes.com/"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, 'lxml')
    nav = soup.find('nav', id='mntl-header-nav_1-0')
    categories = nav.find_all('a', href=True)
    category_links = [category['href'] for category in categories if 'recipes' in category['href']]
    if filter_keyword:
        category_links = [link for link in category_links if filter_keyword in link]
    return category_links


def save_recipe_images(soup, recipe_name):
    image_folder = os.path.join('pics', recipe_name)
    os.makedirs(image_folder, exist_ok=True)
    article_content = soup.find('div', class_='loc article-content')

    if not article_content:
        print("Блок с контентом рецепта не найден.")
        return []

    image_elements = article_content.find_all('img')
    image_paths = []
    image_count = 0

    for img in image_elements:
        img_url = img.get('src')

        if not img_url:
            continue

        if 'srcset' in img.attrs:
            img_url = img['srcset'].split(',')[-1].split()[0]

        img_url = urljoin('https://www.allrecipes.com', img_url)
        img_data = requests.get(img_url).content
        img_name = f"image_{image_count + 1}.jpg"
        img_path = os.path.join(image_folder, img_name)

        with open(img_path, 'wb') as img_file:
            img_file.write(img_data)

        image_paths.append(img_path)
        image_count += 1

    if image_count == 0:
        print("Изображения не найдены для рецепта.")
    else:
        print(f"Всего сохранено изображений: {image_count} для рецепта {recipe_name}")

    return image_paths


def get_recipe_details(recipe_url, recipe_title="No title"):
    if 'undefinedundefined' in recipe_url:
        print(f"Пропуск недействительной ссылки: {recipe_url}")
        return []

    response = requests.get(recipe_url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, 'lxml')
    title = recipe_title if recipe_title != "No title" else (
        soup.find('h1', class_='article-heading').text.strip() if soup.find('h1',
                                                                            class_='article-heading') else 'No title')

    if "gallery" in recipe_url or soup.find('div', class_='comp list-sc'):
        print(f"Найдено вложенное меню рецептов. Парсинг вложенных рецептов.")
        return get_recipes_from_nested_list(soup)

    category = get_category_from_path(soup)

    rating = np.nan
    rating_block = soup.find('div', id='mm-recipes-review-bar_1-0')
    if rating_block:
        rating_value_block = rating_block.find('div', class_='mm-recipes-review-bar__rating')
        if rating_value_block:
            rating = rating_value_block.text.strip()

    prep_time = cook_time = total_time = servings = np.nan
    details_section = soup.find('div', class_='mm-recipes-details__content')
    if details_section:
        details_items = details_section.find_all('div', class_='mm-recipes-details__item')
        for item in details_items:
            label = item.find('div', class_='mm-recipes-details__label').text.strip()
            value = item.find('div', class_='mm-recipes-details__value').text.strip()
            if label == 'Prep Time:':
                prep_time = time_to_minutes(value)
            elif label == 'Cook Time:':
                cook_time = time_to_minutes(value)
            elif label == 'Total Time:':
                total_time = time_to_minutes(value)
            elif label == 'Servings:':
                servings = process_servings(value)

    ingredients = unificate_ingredients(parse_ingredients(soup))
    image_paths = save_recipe_images(soup, title)
    return [[recipe_url, title, category, rating, prep_time, cook_time, total_time,servings, ingredients, ', '.join(image_paths)]]


def parse_ingredients(soup):
    ingredients = []
    ingredients_div = soup.find('div', id='mm-recipes-structured-ingredients_1-0')

    if ingredients_div:
        ingredients_list = ingredients_div.find_all('li', class_='mm-recipes-structured-ingredients__list-item')
        for item in ingredients_list:
            quantity = item.find('span', attrs={'data-ingredient-quantity': 'true'})
            unit = item.find('span', attrs={'data-ingredient-unit': 'true'})
            name = item.find('span', attrs={'data-ingredient-name': 'true'})

            ingredient_text = ""
            if quantity:
                ingredient_text += quantity.text.strip() + " "
            if unit:
                ingredient_text += unit.text.strip() + " "
            if name:
                ingredient_text += name.text.strip()

            if ingredient_text.strip():
                ingredients.append(ingredient_text.strip())

    return ', '.join(ingredients) if ingredients else np.nan


def get_recipes_from_nested_list(soup):
    nested_recipes = []
    recipe_list = soup.find('div', class_='comp list-sc mntl-block article-content list')
    if recipe_list:
        content_list = recipe_list.find('div', class_='comp list-sc__content mntl-sc-page mntl-block')
        if content_list:
            list_items = content_list.find_all('div', class_='comp list-sc-item mntl-block mntl-sc-list-item')
            for item in list_items:
                title_block = item.find('span', class_='mntl-sc-block-heading__text')
                link_block = item.find('div',
                                       class_='comp mntl-sc-block allrecipes-sc-block-featuredlink mntl-sc-block-universal-featured-link mntl-sc-block-universal-featured-link--button')

                if title_block and link_block and link_block.find('a', href=True):
                    recipe_title = title_block.text.strip()
                    recipe_link = link_block.find('a', href=True)['href']

                    if 'undefinedundefined' in recipe_link:
                        print(f"Пропуск рецепта с недействительной ссылкой: {recipe_title}")
                        continue

                    print(f"Парсинг вложенного рецепта: {recipe_title}, ссылка: {recipe_link}")
                    recipe_details = get_recipe_details(recipe_link, recipe_title)
                    nested_recipes.extend(recipe_details)
                else:
                    print(f"Пропуск элемента без заголовка или ссылки.")

        else:
            print("Список контента не найден в рецепте.")
    else:
        print("Рецепт не содержит вложенных элементов.")

    return nested_recipes


def get_recipes_from_category_or_list(category_url):
    recipes_data = []
    response = requests.get(category_url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, 'lxml')

    list_items = soup.find_all('div', class_='mntl-sc-block allrecipes-sc-block-heading mntl-sc-block-heading')

    if list_items:
        for list_item in list_items:
            recipe_title = list_item.find('span', class_='mntl-sc-block-heading__text').text.strip()
            recipe_link = list_item.find_next('a', href=True)['href']

            if 'undefinedundefined' in recipe_link:
                print(f"Пропуск рецепта с недействительной ссылкой: {recipe_title}")
                continue

            print(f"Список рецептов: Переход к рецепту {recipe_title}")
            recipe_details = get_recipe_details(recipe_link, recipe_title)
            recipes_data.extend(recipe_details)
    else:
        recipe_cards = soup.find_all('a', class_='mntl-card-list-items', href=True)
        for card in recipe_cards:
            recipe_url = card['href']

            if 'undefinedundefined' in recipe_url:
                print(f"Пропуск рецепта с недействительной ссылкой: {recipe_url}")
                continue

            print(f"Парсинг рецепта: {recipe_url}")
            recipe_details = get_recipe_details(recipe_url)
            recipes_data.extend(recipe_details)

    return recipes_data


def get_category_from_path(soup):
    category = "No info"
    breadcrumbs = soup.find('ul', class_='comp mntl-universal-breadcrumbs mntl-block type--squirrel breadcrumbs')
    if breadcrumbs:
        breadcrumb_items = breadcrumbs.find_all('li', class_='comp mntl-breadcrumbs__item mntl-block')

        if len(breadcrumb_items) > 1:
            category_span = breadcrumb_items[1].find('span', class_='link__wrapper')
            if category_span:
                category = category_span.text.strip()

    return category
