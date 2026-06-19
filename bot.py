import os
import random
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "ВАШ_ТОКЕН_ЗДЕСЬ")

# ─── МЕНЮ (полные данные из оригинального бота) ─────────────────────────────

ALLERGEN_RU = {
    "Cereals/gluten": "Глютен",
    "Fish": "Рыба",
    "Crustaceans": "Ракообразные",
    "Eggs": "Яйца",
    "Milk": "Молоко",
    "Soybeans": "Соя",
    "Sesame seeds": "Кунжут",
    "Nuts": "Орехи",
    "Molluscs": "Моллюски",
    "Mustard": "Горчица",
    "Sulphur dioxide": "Сульфиты",
    "Pistachio nuts": "Фисташки",
    "Wheat": "Пшеница",
}

CATEGORIES = {
    "cold": "Холодные закуски",
    "hot": "Горячие закуски",
    "salads": "Салаты",
    "brunch": "Бранч",
    "pancakes": "Протеиновые панкейки",
    "maki": "Маки",
    "nigiri": "Нигири",
    "gunkans": "Гунканы",
    "rolls": "Роллы",
    "burgers": "Суши-бургеры",
    "bowls": "Боулы",
    "hot_plates": "Горячие блюда",
    "desserts": "Десерты",
    "drinks": "Напитки",
}

DISHES = [
    # COLD STARTERS
    {"cat": "cold", "name": "Open Salmon Sushi", "price": "8,75 €",
     "ingredients": "Nori seaweed, sushi rice, salmon fillet, spicy sauce, kimchi mayo, unagi, masago roe",
     "allergens": ["Cereals/gluten", "Eggs", "Fish", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    {"cat": "cold", "name": "Open Tuna Sushi", "price": "9,95 €",
     "ingredients": "Nori seaweed, sushi rice, tuna, truffle sauce, truffle ponzu, masago roe, kimchi mayo",
     "allergens": ["Cereals/gluten", "Eggs", "Fish", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    {"cat": "cold", "name": "Salmon and Tuna Tartare on Nori Chips", "price": "15,95 €",
     "ingredients": "Salmon, tuna, avocado, cucumber, Philadelphia cheese, crispy nori chips, masago roe, kimchi-mayo, unagi, lime, sesame, microgreens",
     "allergens": ["Fish", "Milk", "Sesame seeds", "Soybeans"],
     "serving1": "тарелка, вилка, нож",
     "serving2": "тарелка, вилка, нож", "position": "front"},
    {"cat": "cold", "name": "Tuna Tartare with Truffle on Brioche", "price": "12,35 €",
     "ingredients": "Tuna tartare, truffle sauce, toasted brioche bread",
     "allergens": ["Cereals/gluten", "Eggs", "Fish", "Milk", "Sesame seeds", "Soybeans"],
     "serving1": "тарелка, вилка, нож",
     "serving2": "тарелка, вилка, нож", "position": "front"},
    {"cat": "cold", "name": "Tuna Tataki with Truffle Ponzu", "price": "15,75 €",
     "ingredients": "Seared tuna, truffle ponzu sauce, truffle sauce, fresh chives",
     "allergens": ["Cereals/gluten", "Fish", "Soybeans", "Sulphur dioxide"],
     "serving1": "тарелка, вилка, нож",
     "serving2": "тарелка, вилка, нож", "position": "front"},
    # HOT STARTERS
    {"cat": "hot", "name": "Coconut Tempura Shrimp", "price": "9,35 €",
     "ingredients": "Coconut tempura shrimp, sweet wasabi sauce",
     "allergens": ["Cereals/gluten", "Fish"],
     "serving1": "руками (без приборов)",
     "serving2": "руками (без приборов)", "position": "front"},
    {"cat": "hot", "name": "Bao with Tempura Shrimp and Kimchi", "price": "13,85 €",
     "ingredients": "Bao bun, tempura shrimp, kimchi cabbage, yuzu aioli sauce",
     "allergens": ["Cereals/gluten", "Crustaceans", "Eggs", "Milk", "Soybeans"],
     "serving1": "руками (без приборов)",
     "serving2": "руками (без приборов)", "position": "front"},
    {"cat": "hot", "name": "Kimchi Shrimp Skewers", "price": "9,35 €",
     "ingredients": "Shrimp, spicy kimchi sauce",
     "allergens": ["Crustaceans", "Soybeans"],
     "serving1": "руками (без приборов)",
     "serving2": "руками (без приборов)", "position": "front"},
    {"cat": "hot", "name": "Yaki-Tori", "price": "9,35 €",
     "ingredients": "Chicken skewers, teriyaki sauce, sesame",
     "allergens": [],
     "serving1": "руками (без приборов)",
     "serving2": "руками (без приборов)", "position": "front"},
    {"cat": "hot", "name": "Edamame in Kimchi Sauce", "price": "6,50 €",
     "ingredients": "Edamame, kimchi-based sauce",
     "allergens": ["Soybeans"],
     "serving1": "руками + дополнительная миска для шелухи",
     "serving2": "руками + дополнительная миска для шелухи", "position": "front"},
    {"cat": "hot", "name": "Edamame with Maldon Salt and Garlic", "price": "6,50 €",
     "ingredients": "Edamame, garlic, Maldon salt flakes, soy sauce",
     "allergens": ["Soybeans"],
     "serving1": "руками + дополнительная миска для шелухи",
     "serving2": "руками + дополнительная миска для шелухи", "position": "front"},
    {"cat": "hot", "name": "Edamame in Teriyaki Sauce", "price": "7,50 €",
     "ingredients": "Edamame, teriyaki sauce",
     "allergens": ["Cereals/gluten", "Soybeans"],
     "serving1": "руками + дополнительная миска для шелухи",
     "serving2": "руками + дополнительная миска для шелухи", "position": "front"},
    {"cat": "hot", "name": "Balls with Salmon and Cheese", "price": "9,35 €",
     "ingredients": "Salmon, 3 cheeses, hot sauce, bonito, unagi sauce",
     "allergens": ["Cereals/gluten", "Fish", "Milk", "Soybeans"],
     "serving1": "руками (без приборов)",
     "serving2": "руками (без приборов)", "position": "side"},
    # SALADS
    {"cat": "salads", "name": "Salad with Tuna Tataki", "price": "14,85 €",
     "ingredients": "Tuna tataki, avocado, cucumber, Philadelphia cheese, mixed greens, masago, sesame seeds, ground pepper, mild dressing",
     "allergens": ["Fish", "Milk", "Sesame seeds", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи", "position": "front"},
    {"cat": "salads", "name": "Wakame and Mango Salad", "price": "9,95 €",
     "ingredients": "Wakame salad, mango, fresh cucumber, mint, sesame seeds, light dressing",
     "allergens": ["Sesame seeds", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи", "position": "front"},
    {"cat": "salads", "name": "Salad with Shrimp and Mango", "price": "13,35 €",
     "ingredients": "Prawns, garlic, white wine, butter, mango, avocado, mixed greens, red chili, cilantro",
     "allergens": ["Crustaceans", "Fish", "Mustard", "Sulphur dioxide"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи", "position": "front"},
    {"cat": "salads", "name": "Salad with Salmon and Orange", "price": "13,75 €",
     "ingredients": "Mixed greens, salmon fillet, orange segments, cherry tomatoes, Philadelphia cheese, Parmesan, masago, mango-passion fruit dressing, soy sauce",
     "allergens": ["Fish", "Milk", "Mustard", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи", "position": "front"},
    # BRUNCH
    {"cat": "brunch", "name": "Shakshuka with Chorizo", "price": "14,35 €",
     "ingredients": "Eggs, tomato sauce, garlic, paprika, spicy chili, chorizo, feta cheese, toasted bread, cilantro",
     "allergens": ["Cereals/gluten", "Eggs", "Milk"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи", "position": "front"},
    {"cat": "brunch", "name": "Omelette with Eel", "price": "19,75 €",
     "ingredients": "Omelette, eel, Philadelphia cheese, crispy cucumber, cuttlefish ink, masago roe, unagi sauce, white sesame, mixed greens, honey-mustard dressing, cherry tomatoes, dried bonito flakes",
     "allergens": ["Cereals/gluten", "Eggs", "Fish", "Milk", "Mustard", "Soybeans", "Sulphur dioxide"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож", "position": "front"},
    {"cat": "brunch", "name": "Omelette with Scallop and Truffle", "price": "23,35 €",
     "ingredients": "Soft omelet, flamed scallop, Philadelphia cheese, truffle sauce, cucumber, avocado, salmon roe, unagi sauce, green leaves, honey-mustard dressing, cherry tomatoes",
     "allergens": ["Cereals/gluten", "Eggs", "Fish", "Milk", "Mustard", "Sesame seeds", "Soybeans", "Sulphur dioxide"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож", "position": "front"},
    {"cat": "brunch", "name": "Toast with Red Caviar (Keta)", "price": "14,99 €",
     "ingredients": "Toasted bread, salmon caviar, Maldon salted butter, Philadelphia cream cheese",
     "allergens": ["Cereals/gluten", "Fish", "Milk"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож", "position": "front"},
    {"cat": "brunch", "name": "Toast with Philadelphia and Avocado", "price": "8,99 €",
     "ingredients": "Bread, Philadelphia, avocado, cayenne pepper",
     "allergens": ["Cereals/gluten", "Milk"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож", "position": "front"},
    {"cat": "brunch", "name": "Toast with Salmon", "price": "13,35 €",
     "ingredients": "Bread, salmon, avocado cream, salmon caviar, cherry tomatoes, lime peel",
     "allergens": ["Cereals/gluten", "Fish", "Milk"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож", "position": "front"},
    {"cat": "brunch", "name": "Brioche with Teriyaki Salmon", "price": "10,45 €",
     "ingredients": "Brioche, salmon, avocado cream, salad mix, cherry tomatoes, honey-mustard dressing, teriyaki, sesame",
     "allergens": ["Cereals/gluten", "Fish", "Mustard", "Sesame seeds"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож", "position": "front"},
    {"cat": "brunch", "name": "Omelette with Shrimp", "price": "11,75 €",
     "ingredients": "Soft omelet, cooked shrimp, Philadelphia cheese, crispy cucumber, masago roe, wasabi, unagi sauce, white sesame, mixed greens, honey-mustard dressing, cherry tomatoes",
     "allergens": ["Cereals/gluten", "Eggs", "Fish", "Milk", "Mustard", "Sesame seeds", "Soybeans", "Sulphur dioxide"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож", "position": "front"},
    {"cat": "brunch", "name": "Omelette with Salmon Tataki", "price": "14,65 €",
     "ingredients": "Soft omelet, tataki salmon, Philadelphia cheese, fresh avocado, crispy cucumber, masago roe, unagi sauce, sesame, mixed greens, honey-mustard dressing, cherry tomatoes",
     "allergens": ["Cereals/gluten", "Eggs", "Fish", "Milk", "Mustard", "Sesame seeds", "Soybeans", "Sulphur dioxide"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож", "position": "front"},
    # PANCAKES
    {"cat": "pancakes", "name": "Japanese Pancakes Pistachio Berry", "price": "15,35 €",
     "ingredients": "Fluffy Japanese pancakes, pistachio cream, strawberry sauce, pistachio",
     "allergens": ["Eggs", "Milk"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи", "position": "front"},
    {"cat": "pancakes", "name": "Japanese Pancakes Tropical Melt", "price": "15,35 €",
     "ingredients": "Fluffy Japanese pancakes, mango and passion fruit cream, tropical caramel, mango, almond chips",
     "allergens": [],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи", "position": "front"},
    {"cat": "pancakes", "name": "Japanese Pancakes Apple Crunch", "price": "15,35 €",
     "ingredients": "Fluffy Japanese pancakes, caramelized apples, vanilla ice cream, crunchy crumble",
     "allergens": [],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи", "position": "front"},
    # ROLLS (selection)
    {"cat": "rolls", "name": "Philadelphia Roll", "price": "13,75 €",
     "ingredients": "Sushi rice, nori, salmon, Philadelphia cheese, cucumber, sesame",
     "allergens": ["Fish", "Milk", "Sesame seeds"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    {"cat": "rolls", "name": "Dragon Roll", "price": "17,50 €",
     "ingredients": "Tempura shrimp, cucumber, avocado, masago, unagi sauce, sesame",
     "allergens": ["Cereals/gluten", "Crustaceans", "Sesame seeds", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    {"cat": "rolls", "name": "Spicy Tuna Roll", "price": "14,50 €",
     "ingredients": "Tuna, spicy sauce, cucumber, sesame, masago",
     "allergens": ["Fish", "Sesame seeds", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    # HOT PLATES
    {"cat": "hot_plates", "name": "Salmon Teriyaki", "price": "18,75 €",
     "ingredients": "Salmon fillet, teriyaki sauce, sushi rice, sesame, mixed greens",
     "allergens": ["Fish", "Sesame seeds", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож", "position": "front"},
    {"cat": "hot_plates", "name": "Chicken Katsu Curry", "price": "16,50 €",
     "ingredients": "Breaded chicken, Japanese curry sauce, sushi rice, pickled vegetables",
     "allergens": ["Cereals/gluten", "Eggs", "Milk"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож", "position": "front"},
    # DESSERTS
    {"cat": "desserts", "name": "Lemon Ginger Cheesecake", "price": "9,00 €",
     "ingredients": "Delicate cheesecake, creamy texture, lemon, spicy ginger, soft meringue",
     "allergens": ["Eggs", "Milk", "Sulphur dioxide", "Wheat"],
     "serving1": "десертная ложка", "serving2": "десертная ложка", "position": "front"},
    {"cat": "desserts", "name": "Chocolate Fondant", "price": "10,00 €",
     "ingredients": "Mango, passion fruit sauce",
     "allergens": [],
     "serving1": "десертная ложка", "serving2": "десертная ложка", "position": "front"},
    {"cat": "desserts", "name": "Sweet Sakura Sushi", "price": "12,00 €",
     "ingredients": "Thin crepe, strawberry, peach, orange, Milka cream cheese, Philadelphia cheese, mascarpone, cashews, honey, granola, pink chocolate",
     "allergens": ["Cereals/gluten", "Milk", "Nuts"],
     "serving1": "палочки", "serving2": "палочки", "position": "front"},
    # DRINKS
    {"cat": "drinks", "name": "Espresso", "price": "2,20 €",
     "ingredients": "Кофе", "allergens": [],
     "serving1": "блюдце, кофейная ложка, сахар",
     "serving2": "блюдце, кофейная ложка, сахар", "position": "side"},
    {"cat": "drinks", "name": "Cappuccino", "price": "2,80–3,10 €",
     "ingredients": "Espresso, milk foam (cow/coconut/oat milk)",
     "allergens": ["Milk"],
     "serving1": "блюдце, чайная ложка, сахар",
     "serving2": "блюдце, чайная ложка, сахар", "position": "side"},
    {"cat": "drinks", "name": "Espresso Tonic", "price": "5,75 €",
     "ingredients": "Schweppes tonic, double espresso", "allergens": [],
     "serving1": "трубочка, подставка",
     "serving2": "трубочка, подставка", "position": "side"},
    {"cat": "drinks", "name": "Matcha Yuzu Tonic", "price": "7,50 €",
     "ingredients": "Schweppes tonic, yuzu juice, matcha", "allergens": [],
     "serving1": "трубочка, подставка",
     "serving2": "трубочка, подставка", "position": "side"},
    {"cat": "drinks", "name": "Espresso Martini", "price": "10,00 €",
     "ingredients": "Absolut Vanilla, coffee liqueur, espresso", "allergens": [],
     "serving1": "подставка", "serving2": "подставка", "position": "side"},
    {"cat": "drinks", "name": "Tommy's Margarita", "price": "12,00 €",
     "ingredients": "White tequila, lime juice, agave syrup", "allergens": [],
     "serving1": "подставка", "serving2": "подставка", "position": "side"},
    {"cat": "drinks", "name": "Venetian Spritz", "price": "9,00 €",
     "ingredients": "Aperol, Cinzano Spritz, sparkling water, orange lemonade", "allergens": [],
     "serving1": "подставка", "serving2": "подставка", "position": "side"},
    {"cat": "drinks", "name": "Chai Latte", "price": "6,00 €",
     "ingredients": "Black tea, milk, cinnamon, cardamom, oriental spices", "allergens": ["Milk"],
     "serving1": "блюдце, чайная ложка, сахар",
     "serving2": "блюдце, чайная ложка, сахар", "position": "side"},
    {"cat": "drinks", "name": "Strawberry Lemonade", "price": "7,50 €",
     "ingredients": "Strawberry purée, rose lemonade", "allergens": [],
     "serving1": "трубочка, подставка",
     "serving2": "трубочка, подставка", "position": "side"},
    {"cat": "drinks", "name": "Negroni", "price": "10,00 €",
     "ingredients": "London Dry gin, Campari bitter, red vermouth", "allergens": [],
     "serving1": "подставка", "serving2": "подставка", "position": "side"},
]

# ─── ХРАНИЛИЩЕ РЕЗУЛЬТАТОВ (в памяти, можно заменить на БД) ─────────────────
# user_scores[user_id] = {"best": int, "attempts": int, "last_score": int, "name": str}
user_scores = {}

QUIZ_LENGTH = 10  # вопросов за тест


# ─── ГЕНЕРАТОР ВОПРОСОВ ──────────────────────────────────────────────────────

def generate_question(dish: dict, all_dishes: list) -> dict:
    """Возвращает dict с полями: text, options, correct_index, explanation"""
    q_type = random.choice(["allergens", "price", "serving", "ingredient", "category"])

    if q_type == "allergens":
        correct = ", ".join([ALLERGEN_RU.get(a, a) for a in dish["allergens"]]) or "Отсутствуют"
        # Генерируем 3 неправильных варианта
        wrong_dishes = [d for d in all_dishes if d["name"] != dish["name"] and d["allergens"] != dish["allergens"]]
        wrongs = random.sample(wrong_dishes, min(3, len(wrong_dishes)))
        wrong_opts = []
        for wd in wrongs:
            w = ", ".join([ALLERGEN_RU.get(a, a) for a in wd["allergens"]]) or "Отсутствуют"
            if w not in wrong_opts and w != correct:
                wrong_opts.append(w)
        while len(wrong_opts) < 3:
            fallback = random.choice(list(ALLERGEN_RU.values()))
            opt = fallback
            if opt not in wrong_opts and opt != correct:
                wrong_opts.append(opt)
        options = wrong_opts[:3] + [correct]
        random.shuffle(options)
        return {
            "text": f"🍽 *{dish['name']}*\n\nКакие аллергены содержатся в этом блюде?",
            "options": options,
            "correct": correct,
            "explanation": f"✅ Аллергены: *{correct}*\n📋 Состав: {dish['ingredients']}"
        }

    elif q_type == "price":
        correct = dish["price"]
        wrong_dishes = [d for d in all_dishes if d["name"] != dish["name"] and d["price"] != dish["price"]]
        wrongs = random.sample(wrong_dishes, min(3, len(wrong_dishes)))
        wrong_opts = [d["price"] for d in wrongs if d["price"] != correct][:3]
        while len(wrong_opts) < 3:
            wrong_opts.append(f"{random.randint(5, 25)},{'00' if random.random() > 0.5 else '50'} €")
        options = list(set(wrong_opts[:3])) + [correct]
        while len(options) < 4:
            options.append(f"{random.randint(5, 25)},75 €")
        options = list(dict.fromkeys(options))[:4]
        random.shuffle(options)
        return {
            "text": f"🍽 *{dish['name']}*\n_{CATEGORIES.get(dish['cat'], dish['cat'])}_\n\nСколько стоит это блюдо?",
            "options": options,
            "correct": correct,
            "explanation": f"✅ Правильная цена: *{correct}*"
        }

    elif q_type == "serving":
        correct = dish["serving1"]
        wrong_dishes = [d for d in all_dishes if d["serving1"] != dish["serving1"]]
        wrong_opts = list({d["serving1"] for d in wrong_dishes})
        random.shuffle(wrong_opts)
        wrong_opts = wrong_opts[:3]
        while len(wrong_opts) < 3:
            wrong_opts.append("вилка, нож, ложка")
        options = wrong_opts[:3] + [correct]
        random.shuffle(options)
        return {
            "text": f"🍽 *{dish['name']}*\n\nКак подаётся это блюдо для *1 гостя*?",
            "options": options,
            "correct": correct,
            "explanation": f"✅ Подача (1 гость): *{correct}*\n👥 Подача (2+ гостя): {dish['serving2']}"
        }

    elif q_type == "ingredient":
        # Какой ингредиент НЕ входит в блюдо?
        if not dish["ingredients"]:
            return generate_question(dish, all_dishes)  # пробуем другой тип
        ingrs = [i.strip() for i in dish["ingredients"].replace(",", ",").split(",")]
        if len(ingrs) < 2:
            return generate_question(dish, all_dishes)
        # Настоящий ингредиент — входит
        real = random.choice(ingrs)
        # Ложный — из других блюд
        fake_pool = []
        for d in all_dishes:
            if d["name"] != dish["name"] and d["ingredients"]:
                for ing in d["ingredients"].split(","):
                    ing = ing.strip()
                    if ing and ing.lower() not in dish["ingredients"].lower():
                        fake_pool.append(ing)
        if not fake_pool:
            return generate_question(dish, all_dishes)
        fake = random.choice(fake_pool)
        # Вопрос: что входит в состав?
        other_reals = [i for i in ingrs if i != real]
        options_pool = other_reals[:2] + [real, fake]
        random.shuffle(options_pool)
        options = options_pool[:4]
        if real not in options:
            options[0] = real
        random.shuffle(options)
        return {
            "text": f"🍽 *{dish['name']}*\n\nЧто входит в состав этого блюда?\n_(выберите ОДИН ингредиент, который точно есть в блюде)_",
            "options": options,
            "correct": real,
            "explanation": f"✅ Полный состав:\n{dish['ingredients']}"
        }

    else:  # category
        correct = CATEGORIES.get(dish["cat"], dish["cat"])
        wrong_cats = [v for k, v in CATEGORIES.items() if k != dish["cat"]]
        random.shuffle(wrong_cats)
        options = wrong_cats[:3] + [correct]
        random.shuffle(options)
        return {
            "text": f"🍽 *{dish['name']}*\n\nК какой категории меню относится это блюдо?",
            "options": options,
            "correct": correct,
            "explanation": f"✅ Категория: *{correct}*"
        }


def build_quiz_session(n=QUIZ_LENGTH) -> list:
    dishes = random.sample(DISHES, min(n, len(DISHES)))
    questions = [generate_question(d, DISHES) for d in dishes]
    return questions


# ─── ХЕЛПЕРЫ ─────────────────────────────────────────────────────────────────

def score_emoji(score: int, total: int) -> str:
    pct = score / total
    if pct >= 0.9:
        return "🏆"
    elif pct >= 0.7:
        return "⭐"
    elif pct >= 0.5:
        return "👍"
    else:
        return "📚"


def get_user_score(user_id: int) -> dict:
    return user_scores.get(user_id, {"best": 0, "attempts": 0, "last_score": None, "name": ""})


def update_user_score(user_id: int, name: str, score: int, total: int):
    prev = get_user_score(user_id)
    best = max(prev["best"], score)
    user_scores[user_id] = {
        "name": name or prev["name"],
        "best": best,
        "attempts": prev["attempts"] + 1,
        "last_score": score,
        "total": total,
    }


# ─── HANDLERS ────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name or "официант"
    stats = get_user_score(user.id)

    stats_text = ""
    if stats["attempts"] > 0:
        stats_text = (
            f"\n\n📊 *Ваша статистика:*\n"
            f"Попыток: {stats['attempts']}\n"
            f"Лучший результат: {stats['best']}/{QUIZ_LENGTH} {score_emoji(stats['best'], QUIZ_LENGTH)}\n"
            f"Последний результат: {stats['last_score']}/{QUIZ_LENGTH}"
        )

    keyboard = [
        [InlineKeyboardButton("🎯 Начать тест", callback_data="quiz_start")],
        [InlineKeyboardButton("📊 Моя статистика", callback_data="stats")],
        [InlineKeyboardButton("🏆 Таблица лидеров", callback_data="leaderboard")],
    ]
    await update.message.reply_text(
        f"👋 Привет, *{name}*!\n\n"
        f"Я бот для проверки знаний меню *Norico*.\n\n"
        f"Тест состоит из *{QUIZ_LENGTH} вопросов* по:\n"
        f"• Составу блюд\n"
        f"• Аллергенам\n"
        f"• Ценам\n"
        f"• Подаче\n"
        f"• Категориям меню"
        f"{stats_text}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = update.effective_user

    # ── Начать тест ──
    if data == "quiz_start":
        questions = build_quiz_session(QUIZ_LENGTH)
        context.user_data["questions"] = questions
        context.user_data["current"] = 0
        context.user_data["score"] = 0
        context.user_data["wrong_answers"] = []
        await send_question(query.message, context, edit=True)

    # ── Ответ на вопрос ──
    elif data.startswith("ans_"):
        chosen_idx = int(data.split("_")[1])
        questions = context.user_data.get("questions", [])
        current = context.user_data.get("current", 0)

        if current >= len(questions):
            return

        q = questions[current]
        options = q["options"]
        chosen = options[chosen_idx]
        correct = q["correct"]
        is_correct = chosen == correct

        if is_correct:
            context.user_data["score"] += 1
            result_text = f"✅ *Правильно!*\n\n{q['explanation']}"
        else:
            context.user_data["wrong_answers"].append({
                "question": q["text"],
                "your": chosen,
                "correct": correct,
                "explanation": q["explanation"]
            })
            result_text = (
                f"❌ *Неправильно!*\n\n"
                f"Ваш ответ: _{chosen}_\n"
                f"Правильный ответ: *{correct}*\n\n"
                f"{q['explanation']}"
            )

        score_now = context.user_data["score"]
        context.user_data["current"] = current + 1
        next_q = current + 1

        progress = f"Вопрос {current + 1}/{len(questions)} | Счёт: {score_now}"

        if next_q < len(questions):
            keyboard = [[InlineKeyboardButton("➡️ Следующий вопрос", callback_data="next_question")]]
            await query.message.edit_text(
                f"{result_text}\n\n_{progress}_",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            # Тест завершён
            keyboard = [[InlineKeyboardButton("➡️ Посмотреть результат", callback_data="show_result")]]
            await query.message.edit_text(
                f"{result_text}\n\n_{progress}_",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

    # ── Следующий вопрос ──
    elif data == "next_question":
        await send_question(query.message, context, edit=True)

    # ── Показать итог ──
    elif data == "show_result":
        await show_result(query.message, context, user)

    # ── Статистика ──
    elif data == "stats":
        stats = get_user_score(user.id)
        if stats["attempts"] == 0:
            text = "📊 Вы ещё не проходили тест. Начните прямо сейчас!"
        else:
            emoji = score_emoji(stats["best"], QUIZ_LENGTH)
            pct = round(stats["best"] / QUIZ_LENGTH * 100)
            text = (
                f"📊 *Ваша статистика*\n\n"
                f"👤 {stats['name']}\n"
                f"🎯 Попыток: {stats['attempts']}\n"
                f"🏆 Лучший результат: {stats['best']}/{QUIZ_LENGTH} ({pct}%) {emoji}\n"
                f"📝 Последний результат: {stats['last_score']}/{QUIZ_LENGTH}"
            )
        keyboard = [
            [InlineKeyboardButton("🎯 Пройти тест", callback_data="quiz_start")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_main")],
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # ── Таблица лидеров ──
    elif data == "leaderboard":
        if not user_scores:
            text = "🏆 Таблица лидеров пуста — станьте первым!"
        else:
            sorted_users = sorted(user_scores.items(), key=lambda x: x[1]["best"], reverse=True)
            lines = ["🏆 *Таблица лидеров*\n"]
            medals = ["🥇", "🥈", "🥉"]
            for i, (uid, data_u) in enumerate(sorted_users[:10]):
                medal = medals[i] if i < 3 else f"{i+1}."
                name = data_u.get("name", "Аноним")
                best = data_u["best"]
                pct = round(best / QUIZ_LENGTH * 100)
                attempts = data_u["attempts"]
                you = " ← вы" if uid == user.id else ""
                lines.append(f"{medal} *{name}* — {best}/{QUIZ_LENGTH} ({pct}%) | попыток: {attempts}{you}")
            text = "\n".join(lines)
        keyboard = [
            [InlineKeyboardButton("🎯 Пройти тест", callback_data="quiz_start")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_main")],
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # ── Пересдать / Главное меню ──
    elif data == "quiz_retry":
        questions = build_quiz_session(QUIZ_LENGTH)
        context.user_data["questions"] = questions
        context.user_data["current"] = 0
        context.user_data["score"] = 0
        context.user_data["wrong_answers"] = []
        await send_question(query.message, context, edit=True)

    elif data == "back_main":
        stats = get_user_score(user.id)
        stats_text = ""
        if stats["attempts"] > 0:
            stats_text = (
                f"\n\n📊 Лучший результат: *{stats['best']}/{QUIZ_LENGTH}* {score_emoji(stats['best'], QUIZ_LENGTH)}"
            )
        keyboard = [
            [InlineKeyboardButton("🎯 Начать тест", callback_data="quiz_start")],
            [InlineKeyboardButton("📊 Моя статистика", callback_data="stats")],
            [InlineKeyboardButton("🏆 Таблица лидеров", callback_data="leaderboard")],
        ]
        await query.message.edit_text(
            f"🍣 *Тест знаний меню Norico*\n\nВыберите действие:{stats_text}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    # ── Разбор ошибок ──
    elif data == "review_wrong":
        wrong = context.user_data.get("wrong_answers", [])
        if not wrong:
            await query.message.edit_text("✅ Ошибок не было — отличный результат!")
            return
        text = f"📚 *Разбор ошибок ({len(wrong)} шт.)*\n\n"
        for i, w in enumerate(wrong, 1):
            text += (
                f"*{i}.* Вопрос: {w['question'].split(chr(10))[0]}\n"
                f"❌ Ваш ответ: _{w['your']}_\n"
                f"✅ Правильно: *{w['correct']}*\n\n"
            )
        keyboard = [
            [InlineKeyboardButton("🔄 Пересдать тест", callback_data="quiz_retry")],
            [InlineKeyboardButton("◀️ В главное меню", callback_data="back_main")],
        ]
        # Разбиваем на части если слишком длинное
        if len(text) > 4000:
            text = text[:4000] + "\n...(сокращено)"
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def send_question(message, context: ContextTypes.DEFAULT_TYPE, edit: bool = False):
    questions = context.user_data.get("questions", [])
    current = context.user_data.get("current", 0)
    score = context.user_data.get("score", 0)

    if current >= len(questions):
        return

    q = questions[current]
    options = q["options"]

    keyboard = []
    for i, opt in enumerate(options):
        keyboard.append([InlineKeyboardButton(opt, callback_data=f"ans_{i}")])

    progress = f"Вопрос {current + 1}/{len(questions)} | Счёт: {score}"
    text = f"_{progress}_\n\n{q['text']}"

    if edit:
        await message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def show_result(message, context: ContextTypes.DEFAULT_TYPE, user):
    score = context.user_data.get("score", 0)
    questions = context.user_data.get("questions", [])
    total = len(questions)
    wrong = context.user_data.get("wrong_answers", [])
    name = user.first_name or "Аноним"

    update_user_score(user.id, name, score, total)
    stats = get_user_score(user.id)

    pct = round(score / total * 100) if total > 0 else 0
    emoji = score_emoji(score, total)

    if pct >= 90:
        msg = "Превосходно! Вы отлично знаете меню! 🌟"
    elif pct >= 70:
        msg = "Хороший результат! Есть над чем поработать."
    elif pct >= 50:
        msg = "Неплохо, но стоит повторить меню."
    else:
        msg = "Нужно подтянуть знания меню. Не сдавайтесь! 💪"

    is_best = score >= stats["best"]
    best_note = " 🆕 *Новый рекорд!*" if is_best and stats["attempts"] > 1 else ""

    text = (
        f"🎉 *Тест завершён!*{best_note}\n\n"
        f"👤 {name}\n"
        f"✅ Правильных ответов: *{score}/{total}* ({pct}%) {emoji}\n"
        f"❌ Ошибок: {len(wrong)}\n\n"
        f"_{msg}_\n\n"
        f"📊 *Ваш рекорд:* {stats['best']}/{total} | Попыток: {stats['attempts']}"
    )

    keyboard = [
        [InlineKeyboardButton("🔄 Пересдать тест", callback_data="quiz_retry")],
    ]
    if wrong:
        keyboard.append([InlineKeyboardButton("📚 Разобрать ошибки", callback_data="review_wrong")])
    keyboard.append([InlineKeyboardButton("🏆 Таблица лидеров", callback_data="leaderboard")])
    keyboard.append([InlineKeyboardButton("◀️ В главное меню", callback_data="back_main")])

    await message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("BOT ERROR: %s", context.error)


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    app.add_error_handler(error_handler)
    print("Quiz бот запущен...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
