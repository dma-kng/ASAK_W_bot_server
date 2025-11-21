
import os
from flask import Flask, request
import requests
from parser import parse_all_products, analyze_overall_stats, analyze_price_categories
import config

app = Flask(__name__)
TOKEN = config.TELEGRAN_TOKEN
API_URL = f'https://api.telegram.org/bot{TOKEN}/'

user_states = {}

def send_message(chat_id, text):
    url = API_URL + 'sendMessage'
    requests.post(url, json={
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    })


def download_file(file_id, save_path):
    get_file_url = API_URL + f'getFile?file_id={file_id}'
    file_info = requests.get(get_file_url).json()
    file_path_on_server = file_info['result']['file_path']
    file_url = f'https://api.telegram.org/file/bot{TOKEN}/{file_path_on_server}'
    content = requests.get(file_url).content
    with open(save_path, 'wb') as f:
        f.write(content)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if 'message' not in data:
        return 'ok'
    message = data['message']
    chat_id = message['chat']['id']
    user_id = chat_id

    if 'text' in message and message['text'] == '/start':
        send_message(chat_id, 'FFFFFFПривет! Я могу сделать для тебя аналитику по любой категории товаров на Wildberries, просто пришли мне HTML-файл страницы поиска на WB по интересующей категории. (Онлайн запросы через бот, к сожалению, пока не доступны из-за ограничений WB)')
        return 'ok'

    if 'document' in message:
        file_id = message['document']['file_id']
        file_name = message['document']['file_name'] if message['document']['file_name'].endswith('.html') else 'user_input.html'
        save_path = f'temp_{user_id}_{file_name}'
        download_file(file_id, save_path)
        user_states[user_id] = {'file_path': save_path}
        send_message(chat_id, 'Файл сохранён! Теперь пришли название категории или товара.')
        return 'ok'

    if 'text' in message and user_id in user_states and 'file_path' in user_states[user_id]:
        file_path = user_states[user_id]['file_path']
        query = message['text']
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
            send_message(chat_id, report[:4096])
        except Exception as e:
            send_message(chat_id, f'Ошибка обработки файла: {e}')
        try:
            os.remove(file_path)
        except Exception:
            pass
        user_states.pop(user_id, None)
        return 'ok'

    return 'ok'







