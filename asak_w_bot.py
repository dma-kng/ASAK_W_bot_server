# bot_webhook.py
import os
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update

import config
from parser import parse_all_products, analyze_overall_stats, analyze_price_categories

app = Flask(__name__)
bot = Bot(token=config.TELEGRAM_TOKEN)
dp = Dispatcher()

user_states = {}

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.to_object(request.json)
    # Самая простая обработка обновления
    # Можно использовать Dispatcher.feed_update() или вручную вызвать почтовую логику
    # Ниже пример ручной фильтрации

    if update.message:
        message = update.message
        user_id = message.from_user.id

        # Команда /start
        if message.text and message.text == '/start':
            bot.send_message(user_id,
                'Привет! Пришли мне HTML-файл страницы WB, а в подписи или следующим сообщением — название категории.')
            return 'ok', 200

        # Документ
        if message.document:
            file_id = message.document.file_id
            file_name = message.document.file_name if message.document.file_name.endswith('.html') else 'user_input.html'
            file = bot.get_file(file_id)
            file_path = f'temp_{user_id}_{file_name}'
            bot.download_file(file.file_path, file_path)
            user_states[user_id] = {'file_path': file_path}
            bot.send_message(user_id, 'Файл сохранён! Теперь пришли название категории или товара, по которому нужна аналитика.')
            return 'ok', 200

        # Текст запроса
        if message.text and user_id in user_states and 'file_path' in user_states[user_id]:
            file_path = user_states[user_id]['file_path']
            query = message.text
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    html = f.read()
                products = parse_all_products(html)
                overall_stats = analyze_overall_stats(products)
                cats = analyze_price_categories(products)
                report = (
                    f"\nОбщая аналитика по запросу: '{query}'\n"
                    f"Найдено товаров: {overall_stats['num_products']}\n"
                    f"Средняя цена: {overall_stats['avg_price']} руб\n"
                    f"Медианная цена: {overall_stats['median_price']} руб\n"
                    f"Минимальная цена: {overall_stats['min_price']} руб\n"
                    f"Максимальная цена: {overall_stats['max_price']} руб\n"
                    f"Средний рейтинг: {overall_stats['avg_rating']}\n"
                    f"Среднее число отзывов: {overall_stats['avg_reviews']}\n"
                    '\n\nСтатистика по ценовым категориям:'
                )
                for cat, data in cats.items():
                    report += (
                        f"\n\nКатегория: {cat} ({data['count']} товаров)\n"
                        f"Ценовой диапазон: {data['price_min']} — {data['price_max']} руб\n"
                        f"Среднее число отзывов: {data['avg_reviews']}\n"
                        f"Медианное число отзывов: {data['median_reviews']}\n"
                        f"Средний рейтинг: {data['avg_rating']}\n"
                        f"Медианный рейтинг: {data['median_rating']}\n"
                    )
                    pop = data['most_popular']
                    if pop:
                        report += (
                            'Самый популярный товар:\n'
                            f"Название: {pop['name']}\n"
                            f"Цена: {pop['price']} руб\n"
                            f"Отзывов: {pop['reviews']}\n"
                            f"Оценка: {pop['rating']}\n"
                        )
                bot.send_message(user_id, report[:4096])
            except Exception as e:
                bot.send_message(user_id, f'Ошибка обработки файла: {e}')
            try:
                os.remove(file_path)
            except Exception:
                pass
            user_states.pop(user_id, None)
            return 'ok', 200

    return 'ok', 200

