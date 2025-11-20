from bs4 import BeautifulSoup
import statistics
import re

def load_html(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def parse_all_products(html: str) -> list:
    soup = BeautifulSoup(html, 'lxml')
    cards = soup.find_all('article', class_='product-card')
    products = []
    for card in cards:
        price = card.select_one('ins.price__lower-price')
        price = (
            re.sub(r"\D", "", price.get_text()) if price else None
        )
        old_price = card.select_one('del')
        old_price = (
            re.sub(r"\D", "", old_price.get_text()) if old_price else None
        )
        discount = card.select_one('span.percentage-sale')
        discount = discount.get_text(strip=True) if discount else None
        brand = card.select_one('span.product-card__brand')
        brand = brand.get_text(strip=True) if brand else None
        name = card.select_one('span.product-card__name')
        name = name.get_text(strip=True) if name else None
        rating = card.select_one('span.address-rate-mini')
        rating = (
            float(rating.get_text(strip=True).replace(',', '.')) if rating else None
        )
        reviews = card.select_one('span.product-card__count')
        reviews = (
            int(re.sub(r"\D", "", reviews.get_text(strip=True))) if reviews else None
        )
        products.append({
            'brand': brand,
            'name': name,
            'price': int(price) if price else None,
            'old_price': int(old_price) if old_price else None,
            'discount': discount,
            'rating': rating,
            'reviews': reviews,
        })
    return products

def analyze_overall_stats(products: list):
    prices = [p['price'] for p in products if p['price'] is not None]
    ratings = [p['rating'] for p in products if p['rating'] is not None]
    reviews = [p['reviews'] for p in products if p['reviews'] is not None]
    brands = [p['brand'] for p in products if p['brand']]
    stats = {
        'num_products': len(products),
        'avg_price': round(statistics.mean(prices), 2) if prices else None,
        'median_price': round(statistics.median(prices), 2) if prices else None,
        'min_price': min(prices) if prices else None,
        'max_price': max(prices) if prices else None,
        'avg_rating': round(statistics.mean(ratings), 2) if ratings else None,
        'median_rating': round(statistics.median(ratings), 2) if ratings else None,
        'avg_reviews': round(statistics.mean(reviews), 1) if reviews else None,
        'median_reviews': round(statistics.median(reviews), 1) if reviews else None,
        'brands': set(brands),
    }
    return stats

def analyze_price_categories(products: list):
    prods = [p for p in products if p['price'] is not None]
    n = len(prods)
    if n == 0:
        return {}
    prods_sorted = sorted(prods, key=lambda x: x['price'])
    q = n // 4
    econom = prods_sorted[:q]
    luxe = prods_sorted[-q:] if q > 0 else prods_sorted[-1:]
    standard = prods_sorted[q:-q] if n >= 4 else []

    def cat_stats(group):
        prices = [p['price'] for p in group]
        reviews = [p['reviews'] for p in group if p['reviews'] is not None]
        ratings = [p['rating'] for p in group if p['rating'] is not None]

        maxpop, max_item = -1, None
        for p in group:
            pop = (p['rating'] or 0) * (p['reviews'] or 0)
            if pop > maxpop:
                maxpop = pop
                max_item = p
        popular_item = None
        if max_item:
            popular_item = {
                'name': max_item['name'],
                'price': max_item['price'],
                'reviews': max_item['reviews'],
                'rating': max_item['rating'],
            }
        return {
            'count': len(group),
            'price_min': min(prices) if prices else None,
            'price_max': max(prices) if prices else None,
            'avg_reviews': round(statistics.mean(reviews), 1) if reviews else None,
            'median_reviews': round(statistics.median(reviews), 1) if reviews else None,
            'avg_rating': round(statistics.mean(ratings), 2) if ratings else None,
            'median_rating': round(statistics.median(ratings), 2) if ratings else None,
            'most_popular': popular_item,
        }

    return {
        'Эконом': cat_stats(econom),
        'Стандарт': cat_stats(standard),
        'Люкс': cat_stats(luxe),
    }

def print_overall_report(stats: dict, query: str):
    print(f'\nОбщая аналитика по запросу: «{query}»')
    print(f'Найдено товаров: {stats['num_products']}')
    if stats["avg_price"] is not None:
        print(f'Средняя цена: {stats['avg_price']} руб')
        print(f'Медианная цена: {stats['median_price']} руб')
        print(f'Минимальная цена: {stats['min_price']} руб')
        print(f'Максимальная цена: {stats['max_price']} руб')
    else:
        print('Данных о ценах недостаточно.')
    print(f'Средний рейтинг: {stats['avg_rating']}' if stats['avg_rating'] is not None else 'Данных о рейтингах нет.')
    print(f'Медианный рейтинг: {stats['median_rating']}' if stats['median_rating'] is not None else '')
    print(f'Среднее число отзывов: {stats['avg_reviews']}' if stats['avg_reviews'] is not None else 'Данных об отзывах нет.')
    print(f'Медианное число отзывов: {stats['median_reviews']}' if stats['median_reviews'] is not None else '')
    print(f'Бренды на странице: {', '.join(stats['brands']) if stats['brands'] else 'Бренды не найдены'}')

def print_price_categories(analysis):
    print('\nСтатистика по ценовым категориям:')
    for cat, data in analysis.items():
        print(f'\nКатегория: {cat} ({data['count']} товаров)')
        print(f'Ценовой диапазон: {data['price_min']} — {data['price_max']} руб')
        print(f'Среднее число отзывов: {data['avg_reviews']}')
        print(f'Медианное число отзывов: {data['median_reviews']}')
        print(f'Средний рейтинг: {data['avg_rating']}')
        print(f'Медианный рейтинг: {data['median_rating']}')
        pop = data['most_popular']
        if pop:
            print('Самый популярный товар в категории:')
            print(f' Название: {pop['name']}')
            print(f' Цена: {pop['price']} руб')
            print(f' Отзывов: {pop['reviews']}')
            print(f' Средняя оценка: {pop['rating']}')
        else:
            print('В категории нет данных для определения популярного товара.')

if __name__ == '__main__':
    query = 'смартфон'
    html = load_html('смартфоны_wb_local.html')
    products = parse_all_products(html)
    overall_stats = analyze_overall_stats(products)
    print_overall_report(overall_stats, query)
    cats = analyze_price_categories(products)
    print_price_categories(cats)
