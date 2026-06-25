import os
import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# ─── СОСТОЯНИЕ КВИЗА ────────────────────────────────────────────────────────
# quiz_state[user_id] = {
#   "questions": [...],   # список вопросов (15 шт.)
#   "current": int,       # текущий индекс
#   "score": int,         # кол-во правильных
#   "answers": [...]      # история ответов
# }
quiz_state: dict = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "ВАШ_ТОКЕН_ЗДЕСЬ")
ALLOWED_THREAD_ID = 67
# ALLOWED_THREAD_ID убран: бот отвечает во всех чатах и топиках

# ─── ДАННЫЕ МЕНЮ ────────────────────────────────────────────────────────────

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
    "maki": "Маки (6 шт.)",
    "nigiri": "Нигири (2 шт.)",
    "gunkans": "Гунканы (2 шт.)",
    "rolls": "Роллы",
    "burgers": "Суши-бургеры 🆕",
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
     "serving2": "палочки, соевый соус, блюдце",
     "position": "side"},
    {"cat": "cold", "name": "Open Tuna Sushi", "price": "9,95 €",
     "ingredients": "Nori seaweed, sushi rice, tuna, truffle sauce, truffle ponzu, masago roe, kimchi mayo",
     "allergens": ["Cereals/gluten", "Eggs", "Fish", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце",
     "position": "side"},
    {"cat": "cold", "name": "Salmon and Tuna Tartare on Nori Chips", "price": "15,95 €",
     "ingredients": "Salmon, tuna, avocado, cucumber, Philadelphia cheese, crispy nori chips, masago roe, kimchi-mayo, unagi, lime, sesame, microgreens",
     "allergens": ["Fish", "Milk", "Sesame seeds", "Soybeans"],
     "serving1": "тарелка, вилка, нож",
     "serving2": "тарелка, вилка, нож",
     "position": "front"},
    {"cat": "cold", "name": "Tuna Tartare with Truffle on Brioche", "price": "12,35 €",
     "ingredients": "Tuna tartare, truffle sauce, toasted brioche bread",
     "allergens": ["Cereals/gluten", "Eggs", "Fish", "Milk", "Sesame seeds", "Soybeans"],
     "serving1": "тарелка, вилка, нож",
     "serving2": "тарелка, вилка, нож",
     "position": "front"},
    {"cat": "cold", "name": "Tuna Tataki with Truffle Ponzu", "price": "15,75 €",
     "ingredients": "Seared tuna, truffle ponzu sauce, truffle sauce, fresh chives",
     "allergens": ["Cereals/gluten", "Fish", "Soybeans", "Sulphur dioxide"],
     "serving1": "тарелка, вилка, нож",
     "serving2": "тарелка, вилка, нож",
     "position": "front"},

    # HOT STARTERS
    {"cat": "hot", "name": "Coconut Tempura Shrimp", "price": "9,35 €",
     "ingredients": "Coconut tempura shrimp, sweet wasabi sauce",
     "allergens": ["Cereals/gluten", "Fish"],
     "serving1": "руками (без приборов)",
     "serving2": "руками (без приборов)",
     "position": "front"},
    {"cat": "hot", "name": "Bao with Tempura Shrimp and Kimchi (2 шт.)", "price": "13,85 €",
     "ingredients": "Bao bun, tempura shrimp, kimchi cabbage, yuzu aioli sauce",
     "allergens": ["Cereals/gluten", "Crustaceans", "Eggs", "Milk", "Soybeans"],
     "serving1": "руками (без приборов)",
     "serving2": "руками (без приборов)",
     "position": "front"},
    {"cat": "hot", "name": "Kimchi Shrimp Skewers", "price": "9,35 €",
     "ingredients": "Shrimp, spicy kimchi sauce",
     "allergens": ["Crustaceans", "Soybeans"],
     "serving1": "руками (без приборов)",
     "serving2": "руками (без приборов)",
     "position": "front"},
    {"cat": "hot", "name": "Yaki-Tori", "price": "9,35 €",
     "ingredients": "Chicken skewers, teriyaki sauce, sesame",
     "allergens": [],
     "serving1": "руками (без приборов)",
     "serving2": "руками (без приборов)",
     "position": "front"},
    {"cat": "hot", "name": "Edamame in Kimchi Sauce", "price": "6,50 €",
     "ingredients": "Edamame, kimchi-based sauce",
     "allergens": ["Soybeans"],
     "serving1": "руками + дополнительная миска для шелухи",
     "serving2": "руками + дополнительная миска для шелухи",
     "position": "front"},
    {"cat": "hot", "name": "Edamame with Maldon Salt and Garlic", "price": "6,50 €",
     "ingredients": "Edamame, garlic, Maldon salt flakes, soy sauce",
     "allergens": ["Soybeans"],
     "serving1": "руками + дополнительная миска для шелухи",
     "serving2": "руками + дополнительная миска для шелухи",
     "position": "front"},
    {"cat": "hot", "name": "Edamame in Teriyaki Sauce", "price": "7,50 €",
     "ingredients": "Edamame, teriyaki sauce",
     "allergens": ["Cereals/gluten", "Soybeans"],
     "serving1": "руками + дополнительная миска для шелухи",
     "serving2": "руками + дополнительная миска для шелухи",
     "position": "front"},
    {"cat": "hot", "name": "Balls with Salmon and Cheese", "price": "9,35 €",
     "ingredients": "Salmon, 3 cheeses, hot sauce, bonito, unagi sauce",
     "allergens": ["Cereals/gluten", "Fish", "Milk", "Soybeans"],
     "serving1": "руками (без приборов)",
     "serving2": "руками (без приборов)",
     "position": "side"},

    # SALADS
    {"cat": "salads", "name": "Salad with Tuna Tataki", "price": "14,85 €",
     "ingredients": "Tuna tataki, avocado, cucumber, Philadelphia cheese, mixed greens, masago, sesame seeds, ground pepper, mild dressing",
     "allergens": ["Fish", "Milk", "Sesame seeds", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи",
     "position": "front"},
    {"cat": "salads", "name": "Wakame and Mango Salad", "price": "9,95 €",
     "ingredients": "Wakame salad, mango, fresh cucumber, mint, sesame seeds, light dressing",
     "allergens": ["Sesame seeds", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи",
     "position": "front"},
    {"cat": "salads", "name": "Salad with Shrimp and Mango", "price": "13,35 €",
     "ingredients": "Prawns, garlic, white wine, butter, mango, avocado, mixed greens, red chili, cilantro",
     "allergens": ["Crustaceans", "Fish", "Mustard", "Sulphur dioxide"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи",
     "position": "front"},
    {"cat": "salads", "name": "Salad with Salmon and Orange", "price": "13,75 €",
     "ingredients": "Mixed greens, salmon fillet, orange segments, cherry tomatoes, Philadelphia cheese, Parmesan, masago, mango-passion fruit dressing, soy sauce",
     "allergens": ["Fish", "Milk", "Mustard", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи",
     "position": "front"},

    # BRUNCH
    {"cat": "brunch", "name": "Brunch Set 1", "price": "33,33 €",
     "ingredients": "Teriyaki salmon brioche, miso omelette, shrimp and kimchi bao",
     "allergens": ["Cereals/gluten", "Crustaceans", "Eggs", "Fish", "Milk", "Sesame seeds", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож",
     "position": "front"},
    {"cat": "brunch", "name": "Shakshuka with Chorizo", "price": "14,35 €",
     "ingredients": "Eggs, tomato sauce, garlic, paprika, spicy chili, chorizo, feta cheese, toasted bread, cilantro",
     "allergens": ["Cereals/gluten", "Eggs", "Milk"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи",
     "position": "front"},
    {"cat": "brunch", "name": "Omelette with Eel", "price": "19,75 €",
     "ingredients": "Omelette, eel, Philadelphia cheese, crispy cucumber, cuttlefish ink, masago roe, unagi sauce, white sesame, mixed greens, honey-mustard dressing, cherry tomatoes, dried bonito flakes",
     "allergens": ["Cereals/gluten", "Eggs", "Fish", "Milk", "Mustard", "Soybeans", "Sulphur dioxide"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож",
     "position": "front"},
    {"cat": "brunch", "name": "Omelette with Scallop and Truffle", "price": "23,35 €",
     "ingredients": "Soft omelet, flamed scallop, Philadelphia cheese, truffle sauce, cucumber, avocado, salmon roe, unagi sauce, green leaves, honey-mustard dressing, cherry tomatoes",
     "allergens": ["Cereals/gluten", "Eggs", "Fish", "Milk", "Mustard", "Sesame seeds", "Soybeans", "Sulphur dioxide"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож",
     "position": "front"},
    {"cat": "brunch", "name": "Kimchi Tuna Bowl", "price": "12,35 €",
     "ingredients": "Rice, marinated tuna, spicy crab, kimchi cucumber, mango, poached egg, sesame seeds",
     "allergens": ["Crustaceans", "Eggs", "Fish", "Sesame seeds", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи",
     "position": "front"},
    {"cat": "brunch", "name": "Vegetarian Bowl with Quinoa", "price": "12,35 €",
     "ingredients": "Quinoa, shiitake mushrooms, edamame, iceberg lettuce, cherry tomatoes, avocado, poached egg, sesame, hot unagi sauce",
     "allergens": ["Eggs", "Sesame seeds", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи",
     "position": "front"},
    {"cat": "brunch", "name": "Quinoa Bowl with Salmon Fillet", "price": "12,85 €",
     "ingredients": "Quinoa, salmon fillet, mango, avocado, edamame, cherry tomatoes, iceberg lettuce, sesame, spicy unagi sauce",
     "allergens": ["Fish", "Sesame seeds"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи",
     "position": "front"},
    {"cat": "brunch", "name": "Toast with Red Caviar (Keta)", "price": "14,99 €",
     "ingredients": "Toasted bread, salmon caviar, Maldon salted butter, Philadelphia cream cheese",
     "allergens": ["Cereals/gluten", "Fish", "Milk"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож",
     "position": "front"},
    {"cat": "brunch", "name": "Toast with Philadelphia and Avocado", "price": "8,99 €",
     "ingredients": "Bread, Philadelphia, avocado, cayenne pepper",
     "allergens": ["Cereals/gluten", "Milk"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож",
     "position": "front"},
    {"cat": "brunch", "name": "Toast with Salmon", "price": "13,35 €",
     "ingredients": "Bread, salmon, avocado cream, salmon caviar, cherry tomatoes, lime peel",
     "allergens": ["Cereals/gluten", "Fish", "Milk"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож",
     "position": "front"},
    {"cat": "brunch", "name": "Toast with Tuna Tartar", "price": "12,35 €",
     "ingredients": "Bread, tuna, avocado cream, truffle ponzu, avocado, cucumber, truffle paste",
     "allergens": ["Cereals/gluten", "Fish", "Milk"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож",
     "position": "front"},
    {"cat": "brunch", "name": "Toast with Scallop", "price": "17,45 €",
     "ingredients": "Bread, scallop, avocado cream, truffle paste, lime peel, cherry tomatoes, cayenne pepper, unagi sauce",
     "allergens": ["Cereals/gluten", "Milk", "Molluscs"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож",
     "position": "front"},
    {"cat": "brunch", "name": "Tostada con Gambas", "price": "12,99 €",
     "ingredients": "Bread, shrimp, avocado cream, salad mix, cherry tomatoes, honey-mustard sauce",
     "allergens": ["Cereals/gluten", "Crustaceans", "Milk", "Mustard"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож",
     "position": "front"},
    {"cat": "brunch", "name": "Brioche with Teriyaki Salmon", "price": "10,45 €",
     "ingredients": "Brioche, salmon, avocado cream, salad mix, cherry tomatoes, honey-mustard dressing, teriyaki, sesame",
     "allergens": ["Cereals/gluten", "Fish", "Mustard", "Sesame seeds"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож",
     "position": "front"},
    {"cat": "brunch", "name": "Avocado and Salmon Brioche Toast", "price": "13,75 €",
     "ingredients": "Brioche, creamy avocado, poached egg, salmon fillet, lime zest, togarashi spices, keta salmon caviar, hollandaise sauce, arugula, cherry tomatoes, Parmesan, black sesame seeds, honey-mustard dressing",
     "allergens": ["Cereals/gluten", "Eggs", "Fish", "Mustard", "Sesame seeds"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож",
     "position": "front"},
    {"cat": "brunch", "name": "Brunch Set with Salmon", "price": "19,35 €",
     "ingredients": "Lightly salted salmon, creamy avocado, soft brioche bun, boiled egg, fresh salad mix, Philadelphia cheese, Maldon salted butter, avocado cream",
     "allergens": ["Cereals/gluten", "Eggs", "Fish", "Milk", "Sesame seeds"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож",
     "position": "front"},
    {"cat": "brunch", "name": "Omelette with Shrimp", "price": "11,75 €",
     "ingredients": "Soft omelet, cooked shrimp, Philadelphia cheese, crispy cucumber, masago roe, wasabi, unagi sauce, white sesame, mixed greens, honey-mustard dressing, cherry tomatoes",
     "allergens": ["Cereals/gluten", "Eggs", "Fish", "Milk", "Mustard", "Sesame seeds", "Soybeans", "Sulphur dioxide"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож",
     "position": "front"},
    {"cat": "brunch", "name": "Omelette with Salmon Tataki", "price": "14,65 €",
     "ingredients": "Soft omelet, tataki salmon, Philadelphia cheese, fresh avocado, crispy cucumber, masago roe, unagi sauce, sesame, mixed greens, honey-mustard dressing, cherry tomatoes",
     "allergens": ["Cereals/gluten", "Eggs", "Fish", "Milk", "Mustard", "Sesame seeds", "Soybeans", "Sulphur dioxide"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож",
     "position": "front"},
    {"cat": "brunch", "name": "Quinoa Breakfast Bowl", "price": "12,35 €",
     "ingredients": "Quinoa, salmon fillet, poached egg, avocado, sesame, unagi sauce",
     "allergens": ["Eggs", "Fish", "Sesame seeds"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи",
     "position": "front"},
    {"cat": "brunch", "name": "Quinoa Bowl with Eel", "price": "14,35 €",
     "ingredients": "Quinoa, eel, avocado, poached egg, chuka seaweed salad, dried bonito chips, sesame, unagi sauce",
     "allergens": ["Eggs", "Fish", "Sesame seeds"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи",
     "position": "front"},
    {"cat": "brunch", "name": "Fried Eggs with Frankfurters", "price": "9,99 €",
     "ingredients": "Egg, salad mix, cherry tomatoes, honey-mustard dressing, Frankfurt sausage, toast",
     "allergens": ["Cereals/gluten", "Eggs", "Mustard"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож",
     "position": "front"},

    # PANCAKES
    {"cat": "pancakes", "name": "Japanese Pancakes Pistachio Berry (35г белка)", "price": "15,35 €",
     "ingredients": "Fluffy Japanese pancakes, pistachio cream, strawberry sauce, pistachio. Без глютена.",
     "allergens": ["Eggs", "Milk"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи",
     "position": "front"},
    {"cat": "pancakes", "name": "Japanese Pancakes Tropical Melt (35г белка)", "price": "15,35 €",
     "ingredients": "Fluffy Japanese pancakes, mango and passion fruit cream, tropical caramel, mango, almond chips. Без глютена.",
     "allergens": [],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи",
     "position": "front"},
    {"cat": "pancakes", "name": "Japanese Pancakes Apple Crunch (35г белка)", "price": "15,35 €",
     "ingredients": "Fluffy Japanese pancakes, caramelized apples, vanilla ice cream, crunchy crumble.",
     "allergens": [],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи",
     "position": "front"},
    {"cat": "pancakes", "name": "Japanese Pancakes Vanilla Strawberry (35г белка)", "price": "16,35 €",
     "ingredients": "Fluffy Japanese pancakes, vanilla mousse with mascarpone, strawberry sauce, fresh strawberries. Без глютена.",
     "allergens": ["Eggs", "Milk"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи",
     "position": "front"},
    {"cat": "pancakes", "name": "Japanese Pancakes Tiramisu (35г белка)", "price": "16,35 €",
     "ingredients": "Fluffy Japanese pancakes, homemade tiramisu cream, coffee syrup, cocoa powder. Без глютена.",
     "allergens": ["Eggs", "Milk"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи",
     "position": "front"},

    # MAKI
    {"cat": "maki", "name": "Maki with Salmon", "price": "6,35 €",
     "ingredients": "Rice, nori, salmon", "allergens": ["Fish"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    {"cat": "maki", "name": "Maki with Cucumber", "price": "5,35 €",
     "ingredients": "Rice, nori, cucumber", "allergens": [],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    {"cat": "maki", "name": "Avocado Maki", "price": "6,35 €",
     "ingredients": "Rice, nori, avocado", "allergens": [],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    {"cat": "maki", "name": "Tuna Maki", "price": "6,35 €",
     "ingredients": "Rice, nori, tuna", "allergens": [],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    {"cat": "maki", "name": "Shrimp Maki", "price": "6,35 €",
     "ingredients": "Rice, nori, shrimp", "allergens": ["Fish"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},

    # NIGIRI
    {"cat": "nigiri", "name": "Nigiri with Salmon", "price": "5,35 €",
     "ingredients": "Rice, salmon", "allergens": ["Fish"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    {"cat": "nigiri", "name": "Nigiri with Flamed Salmon", "price": "5,35 €",
     "ingredients": "Rice, flambéed salmon", "allergens": ["Fish"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    {"cat": "nigiri", "name": "Nigiri with Tuna", "price": "5,35 €",
     "ingredients": "Rice, tuna", "allergens": ["Fish"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    {"cat": "nigiri", "name": "Nigiri with Eel (Anguilla)", "price": "8,00 €",
     "ingredients": "Rice, eel", "allergens": ["Fish"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    {"cat": "nigiri", "name": "Nigiri with Scallop", "price": "9,35 €",
     "ingredients": "Rice, scallop", "allergens": ["Fish"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    {"cat": "nigiri", "name": "Nigiri Real", "price": "6,35 €",
     "ingredients": "Rice, avocado, keta salmon caviar, nori seaweed", "allergens": ["Fish"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},

    # GUNKANS
    {"cat": "gunkans", "name": "Gunkan with Salmon", "price": "5,35 €",
     "ingredients": "Rice, salmon, Japanese mayonnaise, nori seaweed",
     "allergens": ["Eggs", "Fish"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    {"cat": "gunkans", "name": "Gunkan with Spicy Salmon", "price": "5,35 €",
     "ingredients": "Rice, salmon, spicy Japanese mayonnaise, nori seaweed",
     "allergens": ["Eggs", "Fish", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    {"cat": "gunkans", "name": "Gunkan with Tiger Shrimp", "price": "5,35 €",
     "ingredients": "Rice, tiger prawns, Japanese mayonnaise, nori seaweed",
     "allergens": ["Fish"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    {"cat": "gunkans", "name": "Gunkan with Tuna", "price": "5,00 €",
     "ingredients": "Rice, tuna, Japanese mayonnaise, nori seaweed",
     "allergens": ["Fish"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    {"cat": "gunkans", "name": "Gunkan with Eel (Anguilla)", "price": "6,00 €",
     "ingredients": "Rice, eel, Japanese mayonnaise, nori seaweed",
     "allergens": ["Fish"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    {"cat": "gunkans", "name": "Gunkan with Spicy Eel", "price": "7,00 €",
     "ingredients": "Rice, eel, spicy Japanese mayonnaise, nori seaweed",
     "allergens": ["Eggs", "Fish", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    {"cat": "gunkans", "name": "Gunkan with Scallop", "price": "9,50 €",
     "ingredients": "Rice, scallop, Japanese mayonnaise, nori seaweed",
     "allergens": ["Fish"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},
    {"cat": "gunkans", "name": "Gunkan with Red Caviar", "price": "11,35 €",
     "ingredients": "Rice, red caviar, nori seaweed",
     "allergens": ["Fish"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "side"},

    # SUSHI ROLLS
    {"cat": "rolls", "name": "Philadelphia with Avocado", "price": "14,35 €",
     "ingredients": "Sushi rice, salmon fillet, Philadelphia cheese, avocado, nori seaweed",
     "allergens": ["Fish", "Milk"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Philadelphia Classic with Cucumber", "price": "14,35 €",
     "ingredients": "Sushi rice, salmon fillet, Philadelphia cheese, cucumber, nori seaweed",
     "allergens": ["Fish", "Milk"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Philadelphia Burned", "price": "14,35 €",
     "ingredients": "Rice, salmon fillet, Philadelphia cheese, cucumber, nori seaweed, unagi sauce, sweet wasabi, kimchi-mayo sauce",
     "allergens": ["Cereals/gluten", "Eggs", "Fish", "Milk", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Philadelphia Deluxe", "price": "18,95 €",
     "ingredients": "Sushi rice, salmon fillet, eel, Philadelphia cheese, avocado, nori seaweed, tobiko, unagi sauce",
     "allergens": ["Fish", "Milk", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Philadelphia Deluxe Grill", "price": "18,95 €",
     "ingredients": "Sushi rice, seared salmon fillet, eel, Philadelphia cheese, avocado, nori seaweed, tobiko, unagi sauce",
     "allergens": ["Fish", "Milk", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Philadelphia GOLD", "price": "16,35 €",
     "ingredients": "Salmon, avocado, cucumber, Philadelphia cheese, tobiko, edible gold, nori, rice",
     "allergens": ["Cereals/gluten", "Fish", "Milk", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "⭐ Norico Roll (рекомендация шефа)", "price": "18,35 €",
     "ingredients": "Sushi rice, eel, salmon fillet, avocado, Philadelphia cheese, nori seaweed, masago, spicy sauce, unagi sauce, parmesan",
     "allergens": ["Cereals/gluten", "Eggs", "Fish", "Milk", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Fudji Roll", "price": "13,35 €",
     "ingredients": "Rice, salmon fillet, tamago, cucumber, avocado, nori seaweed, unagi sauce, white sesame seeds",
     "allergens": ["Eggs", "Fish", "Sesame seeds", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Dzitaku Roll", "price": "14,35 €",
     "ingredients": "Rice, shrimp, mango, salmon fillet, avocado, masago, unagi sauce, white sesame, nori seaweed",
     "allergens": ["Crustaceans", "Fish", "Sesame seeds", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "California Sake", "price": "13,35 €",
     "ingredients": "Rice, salmon fillet, avocado, cucumber, nori seaweed, masago, unagi sauce, sweet wasabi, kimchi mayo",
     "allergens": ["Cereals/gluten", "Eggs", "Fish", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "California-Ebby Tempura", "price": "10,35 €",
     "ingredients": "Sushi rice, tempura shrimp, cucumber, masago, nori seaweed, spicy sauce",
     "allergens": ["Cereals/gluten", "Crustaceans", "Eggs", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Queen of California", "price": "15,45 €",
     "ingredients": "Nori, rice, tobiko, cucumber, avocado, salmon, prawns, hot sauce",
     "allergens": ["Fish"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Fish Roll", "price": "14,15 €",
     "ingredients": "Nori, salmon fillet, tuna, cooked shrimp, avocado, masago",
     "allergens": ["Crustaceans", "Fish", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Sake Cheese Roll", "price": "12,95 €",
     "ingredients": "Sushi rice, tempura shrimp, salmon fillet, cucumber, melted cheddar cheese, masago, spicy sauce, crispy onions, nori seaweed",
     "allergens": ["Cereals/gluten", "Crustaceans", "Eggs", "Fish", "Milk", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Brand Ebbi-Unagi", "price": "15,95 €",
     "ingredients": "Sushi rice, shrimp, eel, Philadelphia cheese, cucumber, nori seaweed, sesame seeds, unagi sauce",
     "allergens": ["Crustaceans", "Milk", "Sesame seeds", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Tibetan Sushi", "price": "15,35 €",
     "ingredients": "Sushi rice, shrimp, salmon fillet, mango, Philadelphia and cheddar cheese, nori seaweed, tobiko, unagi sauce, sesame seeds",
     "allergens": ["Cereals/gluten", "Crustaceans", "Fish", "Milk", "Sesame seeds", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Baked Sushi with Salmon", "price": "14,35 €",
     "ingredients": "Sushi rice, fried salmon, mango, Philadelphia cheese, nori seaweed, extra cheese, sesame, unagi sauce",
     "allergens": ["Fish", "Milk", "Sesame seeds", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Baked Sushi with Eel", "price": "15,85 €",
     "ingredients": "Sushi rice, tuna, tiger shrimp, eel, avocado, cucumber, Philadelphia cheese, nori seaweed, extra cheese, unagi sauce",
     "allergens": ["Cereals/gluten", "Crustaceans", "Fish", "Milk", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Baked Flamingo Sushi", "price": "14,35 €",
     "ingredients": "Sushi rice, eel, tiger shrimp, avocado, cucumber, Philadelphia cheese, nori seaweed, wasabi, unagi sauce",
     "allergens": ["Cereals/gluten", "Crustaceans", "Fish", "Milk", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Cani Sushi with Salmon Tartar", "price": "12,95 €",
     "ingredients": "Sushi rice, snow crab, salmon fillet, mango, Philadelphia cheese, nori seaweed, tobiko, creamy kimchi mayonnaise sauce",
     "allergens": ["Crustaceans", "Fish", "Milk", "Sesame seeds", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Tiger Dragon Sushi", "price": "13,35 €",
     "ingredients": "Sushi rice, salmon fillet, shrimp, cucumber, avocado, Philadelphia cheese, nori seaweed, sesame seeds, unagi sauce",
     "allergens": ["Crustaceans", "Fish", "Milk", "Sesame seeds", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Roll New York", "price": "13,35 €",
     "ingredients": "Sushi rice, shrimp, snow crab, salmon fillet, mango, avocado, Philadelphia cheese, nori seaweed, tobiko, spicy mayonnaise, sesame seeds",
     "allergens": ["Crustaceans", "Fish", "Milk", "Sesame seeds", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Double Cheese Salmon Sushi", "price": "15,95 €",
     "ingredients": "Sushi rice, seared salmon, shrimp, avocado, Philadelphia and cheddar cheese, nori seaweed, tobiko, unagi sauce",
     "allergens": ["Cereals/gluten", "Crustaceans", "Fish", "Sesame seeds", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Burnt Eel Sushi", "price": "16,85 €",
     "ingredients": "Sushi rice, caramelized eel, avocado, Philadelphia cheese, nori seaweed, dried bonito flakes, unagi sauce",
     "allergens": ["Cereals/gluten", "Fish", "Milk", "Soybeans"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},
    {"cat": "rolls", "name": "Philadelphia Ikura", "price": "16,95 €",
     "ingredients": "Sushi rice, salmon fillet, avocado, Philadelphia cheese, nori seaweed, keta salmon caviar",
     "allergens": ["Fish", "Milk"],
     "serving1": "палочки, соевый соус, блюдце",
     "serving2": "палочки, соевый соус, блюдце", "position": "front"},

    # SUSHI BURGERS
    {"cat": "burgers", "name": "Sushi Burger with Tuna", "price": "13,65 €",
     "ingredients": "Tuna, wakame, spicy mayonnaise, avocado, crab sticks, panko, nori, rice",
     "allergens": ["Fish"],
     "serving1": "перчатки, соевый соус, блюдце",
     "serving2": "перчатки, соевый соус, блюдце", "position": "front"},
    {"cat": "burgers", "name": "Sushi Burger with Shrimp and Cheddar", "price": "12,65 €",
     "ingredients": "Tempura shrimp, spicy mayonnaise, avocado, cheddar cheese, tobiko roe, unagi sauce, panko, nori, rice",
     "allergens": ["Fish"],
     "serving1": "перчатки, соевый соус, блюдце",
     "serving2": "перчатки, соевый соус, блюдце", "position": "front"},
    {"cat": "burgers", "name": "Sushi Burger with Baked Salmon", "price": "13,65 €",
     "ingredients": "Salmon, cucumber, spicy mayonnaise, cheddar cheese, crunch onion, unagi sauce, panko, rice, nori",
     "allergens": ["Fish"],
     "serving1": "перчатки, соевый соус, блюдце",
     "serving2": "перчатки, соевый соус, блюдце", "position": "front"},
    {"cat": "burgers", "name": "Sushi Burger with Shrimp and Salmon", "price": "14,35 €",
     "ingredients": "Salmon, shrimp, crab sticks, cucumber, tobiko roe, spicy mayonnaise, unagi sauce, Philadelphia cheese, nori, rice, panko",
     "allergens": ["Fish", "Milk"],
     "serving1": "перчатки, соевый соус, блюдце",
     "serving2": "перчатки, соевый соус, блюдце", "position": "front"},

    # BOWLS
    {"cat": "bowls", "name": "Poke Bowl with Salmon", "price": "12,35 €",
     "ingredients": "Rice, salmon fillet, avocado, edamame, mango, chuka salad, spicy unagi sauce",
     "allergens": ["Fish", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи", "position": "front"},
    {"cat": "bowls", "name": "Philadelphia Salmon Bowl", "price": "12,35 €",
     "ingredients": "Rice, salmon, avocado, cucumber, Philadelphia cheese, tobiko, nori seaweed, unagi sauce",
     "allergens": ["Eggs", "Fish", "Milk", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи", "position": "front"},
    {"cat": "bowls", "name": "Poke Bowl with Tuna", "price": "13,35 €",
     "ingredients": "Rice, tuna, avocado, edamame, mango, chuka salad, spicy unagi sauce",
     "allergens": ["Fish", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи", "position": "front"},
    {"cat": "bowls", "name": "Philadelphia Bowl with Tuna", "price": "12,35 €",
     "ingredients": "Rice, tuna, avocado, cucumber, Philadelphia cheese, tobiko, nori seaweed, spicy tartar sauce",
     "allergens": ["Eggs", "Fish", "Milk", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи", "position": "front"},
    {"cat": "bowls", "name": "Poke Bowl with Eel", "price": "15,35 €",
     "ingredients": "Rice, eel, avocado, edamame, mango, chuka salad, unagi sauce",
     "allergens": ["Fish", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи", "position": "front"},
    {"cat": "bowls", "name": "Poke Bowl with Scallop and Mango", "price": "19,35 €",
     "ingredients": "Rice, scallop, avocado, edamame, mango, chuka salad, unagi sauce",
     "allergens": ["Molluscs", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи", "position": "front"},
    {"cat": "bowls", "name": "Poseidon Bowl", "price": "13,35 €",
     "ingredients": "Rice, salmon fillet, tuna, snow crab, shrimp, tobiko, spicy unagi sauce",
     "allergens": ["Crustaceans", "Eggs", "Fish", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи", "position": "front"},
    {"cat": "bowls", "name": "Truffle Bowl", "price": "14,35 €",
     "ingredients": "Rice, flamed salmon, shrimp, avocado, Philadelphia cheese, tobiko, unagi sauce",
     "allergens": ["Crustaceans", "Eggs", "Fish", "Milk", "Sesame seeds", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи", "position": "front"},

    # HOT PLATES
    {"cat": "hot_plates", "name": "Teriyaki Chicken", "price": "11,35 €",
     "ingredients": "Chicken, teriyaki sauce, sushi rice, salad mix, cherry tomatoes, honey-mustard dressing",
     "allergens": ["Cereals/gluten", "Mustard", "Sesame seeds", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи", "position": "front"},
    {"cat": "hot_plates", "name": "Udon with Chicken", "price": "12,75 €",
     "ingredients": "Udon noodles, chicken, egg, vegetables, Asian sauces",
     "allergens": ["Cereals/gluten", "Eggs", "Sesame seeds", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи", "position": "front"},
    {"cat": "hot_plates", "name": "Udon with Shrimp", "price": "12,95 €",
     "ingredients": "Udon noodles, shrimp, vegetables, egg, Asian sauces",
     "allergens": ["Cereals/gluten", "Crustaceans", "Eggs", "Sesame seeds", "Soybeans"],
     "serving1": "вилка, нож",
     "serving2": "тарелки, вилка, нож, ложка для раздачи", "position": "front"},

    # DESSERTS
    {"cat": "desserts", "name": "Десерт «Авокадо»", "price": "9,00 €",
     "ingredients": "Citrus calamansi mousse, savoiardi sponge cake with Cointreau, orange ganache in milk chocolate with chocolate glaze",
     "allergens": ["Milk"],
     "serving1": "десертная ложка", "serving2": "десертная ложка", "position": "front"},
    {"cat": "desserts", "name": "Десерт «Coffee Tiramisu»", "price": "9,00 €",
     "ingredients": "Crunchy golden chocolate cup with dark chocolate lid, white chocolate and coffee mousse, puff pastry, crispy aromatic coffee",
     "allergens": ["Milk"],
     "serving1": "десертная ложка", "serving2": "десертная ложка", "position": "front"},
    {"cat": "desserts", "name": "Десерт Fabergé", "price": "10,00 €",
     "ingredients": "White chocolate shell, smooth white chocolate mousse, rich mango purée",
     "allergens": ["Milk"],
     "serving1": "десертная ложка", "serving2": "десертная ложка", "position": "front"},
    {"cat": "desserts", "name": "Десерт Pistachio", "price": "9,00 €",
     "ingredients": "Delicate mousse, intense pistachio, white chocolate, raspberry, citrus notes",
     "allergens": ["Eggs", "Milk", "Pistachio nuts", "Wheat"],
     "serving1": "десертная ложка", "serving2": "десертная ложка", "position": "front"},
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
    {"cat": "desserts", "name": "Sweet Mangolee Sushi", "price": "12,00 €",
     "ingredients": "Chocolate crepe, mango, passion fruit puree, honey, Philadelphia cheese, mascarpone, almond flakes",
     "allergens": ["Cereals/gluten", "Milk", "Nuts"],
     "serving1": "палочки", "serving2": "палочки", "position": "front"},
    {"cat": "desserts", "name": "Sweet Tropicana Sushi", "price": "12,00 €",
     "ingredients": "Thin crepe, Philadelphia cheese, mascarpone, kiwi, mango, peach, passion fruit puree, pink chocolate, mixed nut mix",
     "allergens": ["Cereals/gluten", "Milk", "Nuts"],
     "serving1": "палочки", "serving2": "палочки", "position": "front"},
    {"cat": "desserts", "name": "Moroccan Sweet Sushi", "price": "12,00 €",
     "ingredients": "Thin crepe, Philadelphia cream cheese, mascarpone, strawberry, peach, kiwi, banana, passion fruit puree, almond flakes, sesame seeds",
     "allergens": ["Cereals/gluten", "Milk", "Nuts"],
     "serving1": "палочки", "serving2": "палочки", "position": "front"},

    # DRINKS
    {"cat": "drinks", "name": "Espresso", "price": "2,20 €",
     "ingredients": "", "allergens": [],
     "serving1": "блюдце, кофейная ложка, сахар",
     "serving2": "блюдце, кофейная ложка, сахар", "position": "side"},
    {"cat": "drinks", "name": "Americano", "price": "2,20 €",
     "ingredients": "", "allergens": [],
     "serving1": "блюдце, чайная ложка, сахар",
     "serving2": "блюдце, чайная ложка, сахар", "position": "side"},
    {"cat": "drinks", "name": "Cappuccino", "price": "2,80–3,10 €",
     "ingredients": "Варианты: коровье, кокосовое, овсяное молоко", "allergens": ["Milk"],
     "serving1": "блюдце, чайная ложка, сахар",
     "serving2": "блюдце, чайная ложка, сахар", "position": "side"},
    {"cat": "drinks", "name": "Latte", "price": "3,50–3,80 €",
     "ingredients": "Варианты: коровье, кокосовое, овсяное молоко", "allergens": ["Milk"],
     "serving1": "блюдце, чайная ложка, сахар",
     "serving2": "блюдце, чайная ложка, сахар", "position": "side"},
    {"cat": "drinks", "name": "Flat White", "price": "3,00–3,30 €",
     "ingredients": "Варианты: коровье, кокосовое, овсяное молоко", "allergens": ["Milk"],
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
    {"cat": "drinks", "name": "Norico (signature cocktail)", "price": "13,00 €",
     "ingredients": "Japanese whisky, Choya yuzu liqueur, Choya extra...", "allergens": [],
     "serving1": "подставка", "serving2": "подставка", "position": "side"},
    {"cat": "drinks", "name": "Tommy's Margarita", "price": "12,00 €",
     "ingredients": "White tequila, lime juice, agave syrup", "allergens": [],
     "serving1": "подставка", "serving2": "подставка", "position": "side"},
    {"cat": "drinks", "name": "Daiquiri", "price": "10,00 €",
     "ingredients": "White rum, lime juice, sugar syrup", "allergens": [],
     "serving1": "подставка", "serving2": "подставка", "position": "side"},
    {"cat": "drinks", "name": "Negroni", "price": "10,00 €",
     "ingredients": "London Dry gin, Campari bitter, red vermouth", "allergens": [],
     "serving1": "подставка", "serving2": "подставка", "position": "side"},
    {"cat": "drinks", "name": "Venetian Spritz", "price": "9,00 €",
     "ingredients": "Aperol, Cinzano Spritz, sparkling water, orange lemonade", "allergens": [],
     "serving1": "подставка", "serving2": "подставка", "position": "side"},
    {"cat": "drinks", "name": "Porn Star Martini", "price": "13,00 €",
     "ingredients": "Absolut Vanilla, Passion Fruit Purée, Honey Syrup, Lime...", "allergens": [],
     "serving1": "подставка", "serving2": "подставка", "position": "side"},
    {"cat": "drinks", "name": "Chai Latte", "price": "6,00 €",
     "ingredients": "Black tea, milk, cinnamon, cardamom, oriental spices", "allergens": ["Milk"],
     "serving1": "блюдце, чайная ложка, сахар",
     "serving2": "блюдце, чайная ложка, сахар", "position": "side"},
    {"cat": "drinks", "name": "Raspberry Tea (чайник)", "price": "8,00 €",
     "ingredients": "Raspberry purée, Monin orgat syrup, orange, lime, rosemary", "allergens": [],
     "serving1": "блюдце, чашка, ложка, сахар",
     "serving2": "блюдце, чашки, ложки, сахар", "position": "side"},
    {"cat": "drinks", "name": "Peach Tea (чайник)", "price": "8,00 €",
     "ingredients": "Monin peach purée, lemon, honey, black tea concentrate", "allergens": [],
     "serving1": "блюдце, чашка, ложка, сахар",
     "serving2": "блюдце, чашки, ложки, сахар", "position": "side"},
    {"cat": "drinks", "name": "Strawberry Lemonade", "price": "7,50 €",
     "ingredients": "Strawberry purée, rose lemonade", "allergens": [],
     "serving1": "трубочка, подставка",
     "serving2": "трубочка, подставка", "position": "side"},
    {"cat": "drinks", "name": "Sober Porn Star Martini", "price": "8,00 €",
     "ingredients": "Aloe water, passion fruit, sugar syrup, fresh lemon, pineapple juice, pasteurized egg white",
     "allergens": ["Eggs"],
     "serving1": "подставка", "serving2": "подставка", "position": "side"},
    {"cat": "drinks", "name": "Cava Mont Paral brut", "price": "6,00 € / 30,00 €",
     "ingredients": "Blend of Xarel·lo, Macabeo, Parellada and Garnacha", "allergens": [],
     "serving1": "подставка", "serving2": "ведёрко для льда, подставка", "position": "side"},
    {"cat": "drinks", "name": "Moët Champagne", "price": "60,00 €",
     "ingredients": "", "allergens": [],
     "serving1": "ведёрко для льда, подставка",
     "serving2": "ведёрко для льда, подставка", "position": "side"},
]

# ─── ПОИСК ──────────────────────────────────────────────────────────────────

def search_dishes(query: str) -> list:
    q = query.lower().strip()
    results = []
    for d in DISHES:
        name_score = 0
        if q in d["name"].lower():
            name_score = 2 if d["name"].lower().startswith(q) else 1
        ingr_score = 1 if q in d["ingredients"].lower() else 0
        score = name_score * 2 + ingr_score
        if score > 0:
            results.append((score, d))
    results.sort(key=lambda x: -x[0])
    return [d for _, d in results]

def format_dish(d: dict) -> str:
    pos_emoji = "⬆️ перед гостем (front)" if d["position"] == "front" else "➡️ сбоку (side)"
    allergens_ru = [ALLERGEN_RU.get(a, a) for a in d["allergens"]]
    allergens_str = ", ".join(allergens_ru) if allergens_ru else "отсутствуют"
    cat_name = CATEGORIES.get(d["cat"], d["cat"])

    text = (
        f"🍽 *{d['name']}*\n"
        f"_{cat_name}_ — {d['price']}\n\n"
    )
    if d["ingredients"]:
        text += f"📋 *Состав:*\n{d['ingredients']}\n\n"
    text += (
        f"⚠️ *Аллергены:* {allergens_str}\n\n"
        f"🥢 *Подача при 1 госте:*\n{d['serving1']}\n\n"
        f"👥 *Подача при 2+ гостях:*\n{d['serving2']}\n\n"
        f"📍 *Позиция на столе:* {pos_emoji}"
    )
    return text

# ─── HANDLERS ───────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(
        "START: chat_type=%s thread_id=%s text=%s",
        update.message.chat.type if update.message else None,
        update.message.message_thread_id if update.message else None,
        update.message.text if update.message else None,
    )
    keyboard = [
        [InlineKeyboardButton("🥗 Закуски", callback_data="cat_cold"),
         InlineKeyboardButton("🔥 Горячие закуски", callback_data="cat_hot")],
        [InlineKeyboardButton("🥗 Салаты", callback_data="cat_salads"),
         InlineKeyboardButton("🍳 Бранч", callback_data="cat_brunch")],
        [InlineKeyboardButton("🥞 Панкейки", callback_data="cat_pancakes"),
         InlineKeyboardButton("🌿 Маки", callback_data="cat_maki")],
        [InlineKeyboardButton("🍣 Нигири", callback_data="cat_nigiri"),
         InlineKeyboardButton("🫙 Гунканы", callback_data="cat_gunkans")],
        [InlineKeyboardButton("🍱 Роллы", callback_data="cat_rolls"),
         InlineKeyboardButton("🍔 Суши-бургеры", callback_data="cat_burgers")],
        [InlineKeyboardButton("🥣 Боулы", callback_data="cat_bowls"),
         InlineKeyboardButton("🍜 Горячие блюда", callback_data="cat_hot_plates")],
        [InlineKeyboardButton("🍮 Десерты", callback_data="cat_desserts"),
         InlineKeyboardButton("🍹 Напитки", callback_data="cat_drinks")],
        [InlineKeyboardButton("📝 Пройти тест на знание меню", callback_data="start_quiz")],
    ]
    await update.message.reply_text(
        "👋 Привет! Я справочник Norico.\n\n"
        "Напишите название блюда или ингредиент — я найду всё нужное.\n"
        "Или выберите категорию 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    thread_id = update.message.message_thread_id
    chat_type = update.message.chat.type

    logger.info(
        "TEXT: chat_type=%s thread_id=%s text=%s",
        chat_type,
        thread_id,
        update.message.text
    )

    if chat_type in ("group", "supergroup") and thread_id != ALLOWED_THREAD_ID:
        return

    # Поиск работает во всех чатах и топиках.
    # Фильтр по ALLOWED_THREAD_ID убран, потому что из-за него бот мог молча игнорировать текст.
    logger.info(
        "TEXT MESSAGE: chat_type=%s thread_id=%s text=%s",
        update.message.chat.type,
        update.message.message_thread_id,
        update.message.text,
    )
    query = update.message.text.strip()
    if not query or len(query) < 2:
        await update.message.reply_text("Введите название блюда или ингредиент (минимум 2 символа).")
        return

    results = search_dishes(query)

    if not results:
        await update.message.reply_text(
            f"😕 По запросу *«{query}»* ничего не найдено.\n\n"
            "Попробуйте другое название или используйте /menu для выбора категории.",
            parse_mode="Markdown"
        )
        return

    if len(results) == 1:
        await update.message.reply_text(format_dish(results[0]), parse_mode="Markdown")
        return

    # Несколько результатов — показываем кнопки
    keyboard = []
    for d in results[:10]:
        cat_name = CATEGORIES.get(d["cat"], d["cat"])
        keyboard.append([InlineKeyboardButton(
            f"{d['name']} — {d['price']}",
            callback_data=f"dish_{DISHES.index(d)}"
        )])

    text = f"🔍 По запросу *«{query}»* найдено {len(results)} блюд"
    if len(results) > 10:
        text += " (показаны первые 10)"
    text += ". Выберите:"

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # сначала проверяем квиз
    if await handle_quiz_callback(update, context):
        return

    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("dish_"):
        idx = int(data.split("_")[1])
        dish = DISHES[idx]
        await query.message.reply_text(format_dish(dish), parse_mode="Markdown")

    elif data.startswith("cat_"):
        cat = data[4:]
        cat_dishes = [d for d in DISHES if d["cat"] == cat]
        cat_name = CATEGORIES.get(cat, cat)

        keyboard = []
        for d in cat_dishes:
            keyboard.append([InlineKeyboardButton(
                f"{d['name']} — {d['price']}",
                callback_data=f"dish_{DISHES.index(d)}"
            )])
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_main")])

        await query.message.reply_text(
            f"📂 *{cat_name}* — {len(cat_dishes)} позиций.\nВыберите блюдо:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data == "start_quiz":
        # генерируем квиз как будто из команды
        uid = update.effective_user.id
        questions = generate_quiz()
        quiz_state[uid] = {"questions": questions, "current": 0, "score": 0, "answers": []}
        await query.message.reply_text(
            "🎯 *Тест на знание меню Norico*\n\n"
            f"Всего *{QUIZ_TOTAL} вопросов* по 5 категориям:\n"
            f"• {QUIZ_CATEGORIES['ingredients']}\n"
            f"• {QUIZ_CATEGORIES['allergens']}\n"
            f"• {QUIZ_CATEGORIES['serving']}\n"
            f"• {QUIZ_CATEGORIES['category']}\n"
            f"• {QUIZ_CATEGORIES['bar']}\n\n"
            "Выбирайте один вариант ответа.\nУдачи! 🍀",
            parse_mode="Markdown"
        )
        q = questions[0]
        text, markup = format_quiz_question(q, 0, QUIZ_TOTAL)
        await query.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")

    elif data == "back_main":
        keyboard = [
            [InlineKeyboardButton("🥗 Закуски", callback_data="cat_cold"),
             InlineKeyboardButton("🔥 Горячие закуски", callback_data="cat_hot")],
            [InlineKeyboardButton("🥗 Салаты", callback_data="cat_salads"),
             InlineKeyboardButton("🍳 Бранч", callback_data="cat_brunch")],
            [InlineKeyboardButton("🥞 Панкейки", callback_data="cat_pancakes"),
             InlineKeyboardButton("🌿 Маки", callback_data="cat_maki")],
            [InlineKeyboardButton("🍣 Нигири", callback_data="cat_nigiri"),
             InlineKeyboardButton("🫙 Гунканы", callback_data="cat_gunkans")],
            [InlineKeyboardButton("🍱 Роллы", callback_data="cat_rolls"),
             InlineKeyboardButton("🍔 Суши-бургеры", callback_data="cat_burgers")],
            [InlineKeyboardButton("🥣 Боулы", callback_data="cat_bowls"),
             InlineKeyboardButton("🍜 Горячие блюда", callback_data="cat_hot_plates")],
            [InlineKeyboardButton("🍮 Десерты", callback_data="cat_desserts"),
             InlineKeyboardButton("🍹 Напитки", callback_data="cat_drinks")],
            [InlineKeyboardButton("📝 Пройти тест на знание меню", callback_data="start_quiz")],
        ]
        await query.message.reply_text(
            "Выберите категорию:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# ─── ГЕНЕРАЦИЯ ВОПРОСОВ КВИЗА ───────────────────────────────────────────────

QUIZ_CATEGORIES = {
    "ingredients": "🥢 Состав блюда",
    "allergens":   "⚠️ Аллергены",
    "serving":     "🍽 Подача",
    "category":    "📂 Категория блюда",
    "bar":         "🍹 Бар",
}

QUIZ_QUESTIONS_PER_CATEGORY = 5
QUIZ_TOTAL = 25  # 5 категорий × 5 вопросов


def _make_ingredient_question(dish: dict) -> dict:
    """Какой ингредиент ВХОДИТ в состав блюда?"""
    correct_raw = dish["ingredients"]
    # выбираем один реальный ингредиент из блюда
    parts = [p.strip() for p in correct_raw.split(",") if p.strip()]
    correct_ingr = random.choice(parts)

    # собираем ложные варианты из других блюд
    other_ingrs = []
    for d in DISHES:
        if d["name"] != dish["name"] and d["ingredients"]:
            for p in d["ingredients"].split(","):
                p = p.strip()
                if p and p.lower() not in correct_raw.lower() and p not in other_ingrs:
                    other_ingrs.append(p)
    random.shuffle(other_ingrs)
    wrong = other_ingrs[:3]

    options = [correct_ingr] + wrong
    random.shuffle(options)
    return {
        "type": "ingredients",
        "dish": dish["name"],
        "question": f'Какой ингредиент входит в состав *{dish["name"]}*?',
        "options": options,
        "correct": correct_ingr,
    }


def _make_allergen_question(dish: dict) -> dict:
    """Какой аллерген присутствует в блюде?"""
    all_allergens = list(ALLERGEN_RU.values())

    if dish["allergens"]:
        correct_en = random.choice(dish["allergens"])
        correct_ru = ALLERGEN_RU.get(correct_en, correct_en)
        # 3 ложных: аллергены, которых НЕТ в блюде
        dish_allergens_ru = {ALLERGEN_RU.get(a, a) for a in dish["allergens"]}
        pool = [a for a in all_allergens if a not in dish_allergens_ru]
        wrong = random.sample(pool, min(3, len(pool)))
        question = f'Какой аллерген *содержится* в блюде *{dish["name"]}*?'
    else:
        # в блюде нет аллергенов → спрашиваем, какого нет
        correct_ru = "Нет аллергенов"
        wrong = random.sample(all_allergens, 3)
        question = f'Что верно про аллергены в блюде *{dish["name"]}*?'

    options = [correct_ru] + wrong
    random.shuffle(options)
    return {
        "type": "allergens",
        "dish": dish["name"],
        "question": question,
        "options": options,
        "correct": correct_ru,
    }


def _make_serving_question(dish: dict) -> dict:
    """Как подаётся блюдо одному гостю?"""
    correct = dish["serving1"]
    # собираем другие варианты подачи из меню
    pool = list({d["serving1"] for d in DISHES if d["serving1"] != correct})
    random.shuffle(pool)
    wrong = pool[:3]
    if len(wrong) < 3:
        wrong += ["вилка, нож, ложка"] * (3 - len(wrong))

    options = [correct] + wrong
    random.shuffle(options)
    return {
        "type": "serving",
        "dish": dish["name"],
        "question": f'Как подаётся *{dish["name"]}* одному гостю?',
        "options": options,
        "correct": correct,
    }


def _make_category_question(dish: dict) -> dict:
    """К какой категории меню относится блюдо?"""
    correct = CATEGORIES.get(dish["cat"], dish["cat"])
    # 3 ложных категории
    pool = [v for k, v in CATEGORIES.items() if k != dish["cat"]]
    random.shuffle(pool)
    wrong = pool[:3]

    options = [correct] + wrong
    random.shuffle(options)
    return {
        "type": "category",
        "dish": dish["name"],
        "question": f'В какой раздел меню входит *{dish["name"]}*?',
        "options": options,
        "correct": correct,
    }


def _make_bar_question(drink: dict) -> dict:
    """Какой ингредиент входит в состав напитка/коктейля?"""
    correct_raw = drink["ingredients"]
    parts = [p.strip() for p in correct_raw.split(",") if p.strip()]
    correct_ingr = random.choice(parts)

    # ложные варианты — ингредиенты других напитков, которых нет в этом
    other_ingrs = []
    for d in DISHES:
        if d["cat"] == "drinks" and d["name"] != drink["name"] and d["ingredients"]:
            for p in d["ingredients"].split(","):
                p = p.strip()
                if p and p.lower() not in correct_raw.lower() and p not in other_ingrs:
                    other_ingrs.append(p)
    random.shuffle(other_ingrs)
    wrong = other_ingrs[:3]
    # если барных ингредиентов не хватает — добираем из кухни
    if len(wrong) < 3:
        kitchen_ingrs = []
        for d in DISHES:
            if d["cat"] != "drinks" and d["ingredients"]:
                for p in d["ingredients"].split(","):
                    p = p.strip()
                    if p and p.lower() not in correct_raw.lower() and p not in wrong and p not in kitchen_ingrs:
                        kitchen_ingrs.append(p)
        random.shuffle(kitchen_ingrs)
        wrong += kitchen_ingrs[:3 - len(wrong)]

    options = [correct_ingr] + wrong
    random.shuffle(options)
    return {
        "type": "bar",
        "dish": drink["name"],
        "question": f'Какой ингредиент входит в состав *{drink["name"]}*?',
        "options": options,
        "correct": correct_ingr,
    }


def generate_quiz() -> list:
    """Генерирует 25 вопросов: 5 по составу, 5 по аллергенам, 5 по подаче, 5 по категории, 5 бар."""
    dishes_with_allergens = [d for d in DISHES if d["allergens"]]
    dishes_for_serving = [d for d in DISHES if d["serving1"]]
    # напитки с заполненным составом
    drinks_with_ingr = [d for d in DISHES if d["cat"] == "drinks" and d["ingredients"]]

    # исключаем напитки из общих категорий вопросов, чтобы не пересекались с баром
    non_drinks = [d for d in DISHES if d["cat"] != "drinks"]
    non_drinks_allergens = [d for d in non_drinks if d["allergens"]]

    sample_ingr     = random.sample(non_drinks, min(QUIZ_QUESTIONS_PER_CATEGORY, len(non_drinks)))
    sample_allerg   = random.sample(non_drinks_allergens, min(QUIZ_QUESTIONS_PER_CATEGORY, len(non_drinks_allergens)))
    sample_serving  = random.sample(non_drinks, min(QUIZ_QUESTIONS_PER_CATEGORY, len(non_drinks)))
    sample_category = random.sample(non_drinks, min(QUIZ_QUESTIONS_PER_CATEGORY, len(non_drinks)))
    sample_bar      = random.sample(drinks_with_ingr, min(QUIZ_QUESTIONS_PER_CATEGORY, len(drinks_with_ingr)))

    questions = (
        [_make_ingredient_question(d) for d in sample_ingr] +
        [_make_allergen_question(d)   for d in sample_allerg] +
        [_make_serving_question(d)    for d in sample_serving] +
        [_make_category_question(d)   for d in sample_category] +
        [_make_bar_question(d)        for d in sample_bar]
    )
    random.shuffle(questions)
    return questions


def format_quiz_question(q: dict, idx: int, total: int) -> tuple[str, InlineKeyboardMarkup]:
    cat_label = QUIZ_CATEGORIES.get(q["type"], q["type"])
    text = (
        f"📝 *Вопрос {idx + 1} из {total}* — {cat_label}\n\n"
        f"{q['question']}"
    )
    keyboard = []
    for i, opt in enumerate(q["options"]):
        keyboard.append([InlineKeyboardButton(opt, callback_data=f"qz_{i}")])
    keyboard.append([InlineKeyboardButton("❌ Завершить квиз", callback_data="qz_stop")])
    return text, InlineKeyboardMarkup(keyboard)


# ─── ХЭНДЛЕРЫ КВИЗА ─────────────────────────────────────────────────────────

async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    questions = generate_quiz()
    quiz_state[uid] = {"questions": questions, "current": 0, "score": 0, "answers": []}

    await update.message.reply_text(
        "🎯 *Тест на знание меню Norico*\n\n"
        f"Всего *{QUIZ_TOTAL} вопросов* по 5 категориям:\n"
        f"• {QUIZ_CATEGORIES['ingredients']}\n"
        f"• {QUIZ_CATEGORIES['allergens']}\n"
        f"• {QUIZ_CATEGORIES['serving']}\n"
        f"• {QUIZ_CATEGORIES['category']}\n"
        f"• {QUIZ_CATEGORIES['bar']}\n\n"
        "Выбирайте один вариант ответа.\nУдачи! 🍀",
        parse_mode="Markdown"
    )

    q = questions[0]
    text, markup = format_quiz_question(q, 0, QUIZ_TOTAL)
    await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")


async def handle_quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Обрабатывает ответы квиза. Возвращает True если это был квиз-колбэк."""
    query = update.callback_query
    data = query.data
    uid = update.effective_user.id

    if not (data.startswith("qz_") and uid in quiz_state):
        return False

    await query.answer()
    state = quiz_state[uid]

    if data == "qz_stop":
        score = state["score"]
        done = state["current"]
        del quiz_state[uid]
        await query.message.reply_text(
            f"⏹ Тест прерван.\n\n"
            f"Правильных ответов: *{score} из {done}*",
            parse_mode="Markdown"
        )
        return True

    questions = state["questions"]
    idx = state["current"]
    q = questions[idx]

    chosen_i = int(data.split("_")[1])
    chosen = q["options"][chosen_i]
    is_correct = (chosen == q["correct"])

    if is_correct:
        state["score"] += 1
        feedback = f"✅ *Верно!*"
    else:
        feedback = f"❌ *Неверно.*\nПравильный ответ: _{q['correct']}_"

    state["answers"].append({"q": q["question"], "correct": is_correct})
    state["current"] += 1
    next_idx = state["current"]

    # редактируем сообщение с вопросом → показываем фидбэк
    await query.message.edit_text(
        f"*Вопрос {idx + 1} из {QUIZ_TOTAL}*\n{q['question']}\n\n{feedback}",
        parse_mode="Markdown"
    )

    if next_idx >= QUIZ_TOTAL:
        # тест завершён
        score = state["score"]
        del quiz_state[uid]

        pct = round(score / QUIZ_TOTAL * 100)
        if pct >= 80:
            grade = "🏆 Отлично!"
        elif pct >= 60:
            grade = "👍 Хорошо"
        elif pct >= 40:
            grade = "📚 Нужно подтянуть"
        else:
            grade = "😬 Меню требует изучения"

        await query.message.reply_text(
            f"🎉 *Тест завершён!*\n\n"
            f"Правильных ответов: *{score} из {QUIZ_TOTAL}* ({pct}%)\n"
            f"{grade}\n\n"
            f"Чтобы пройти снова — /quiz",
            parse_mode="Markdown"
        )
    else:
        nq = questions[next_idx]
        text, markup = format_quiz_question(nq, next_idx, QUIZ_TOTAL)
        await query.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")

    return True


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("BOT ERROR. update=%s", update, exc_info=context.error)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_error_handler(error_handler)
    print("Бот запущен...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
