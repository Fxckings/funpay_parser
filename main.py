import json
import requests
from bs4 import BeautifulSoup
import logging
from colorama import Fore, Style, init
import re
from collections import Counter
from tabulate import tabulate
from datetime import datetime

init()
USER_LIST_FILE = 'userdata.json'

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_user_data(user_id):
    """
    Функция для получения данных пользователя.
    """
    try:
        response = requests.get(f"https://funpay.com/users/{user_id}/", timeout=5)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе данных пользователя: {e}")
        return None

def parse_reviews_count(soup):
    """
    парсит кол-во отзывов
    """
    element = soup.find("div", {"class": "rating-full-count"})
    if element:
        return element.text.strip().replace("Всего ", "").replace("отзыв", "").replace('а', '').replace('ов', '').strip()
    if not element:
        sec_element = soup.find("div", {"class": "text-mini text-light mb5"})
        return sec_element.text.strip()
    return "Неизвестно"

def parse_most_popular_game4reviews(soup):
    """
    самые популярные игры по отзывам #TODO парсит 25 отзывов, а и то меньше, чем надо, фикситб
    """
    elements = soup.find_all("div", {"class": "review-item-user"})
    
    games = []
    for element in elements:
        game_with_price = element.find("div", {"class": "review-item-detail"}).text.strip()

        game_name = game_with_price.split(",")[0].strip()

        games.append(game_name)

    game_popularity = Counter(games)

    top_games = game_popularity.most_common(3)

    logging.info(f"Получено кол-во отзывов: {Fore.GREEN} {len(elements)} {Style.RESET_ALL}")
    return [f"{game[0]} - {game[1]}" for game in top_games]

def parse_username(soup):
    """
    парсит имя пользователя
    """
    element = soup.find("span", {"class": "mr4"})
    if element:
        return element.text.strip()
    return "Неизвестно"

def parse_estimation(soup):
    """
    парсит оценку пользователя
    """
    element = soup.find("span", {"class": "big"})
    if element:
        return element.text.replace(' ', '').strip()
    return "Неизвестно"

def parse_registration_date(soup):
    """
    парсит дату регистрации пользователя
    """
    element = soup.find("div", {"class": "text-nowrap"})
    if element:
        return ' '.join(element.text.split())
    return "Неизвестно"

def parse_offers_count(soup):
    """
    парсит кол-во предложений (категорий/игр)
    """
    offers = soup.find_all("div", {"class": "offer"})
    return len(offers) - 1 #1 offer это отзывы)

def parse_lot_count(soup):
    """
    парсит кол-во лотов
    """
    return len(soup.find_all("a", {"class": "tc-item"}))

def parse_status(soup):
    """
    парсит статус пользователя
    """
    element = soup.find("div", {"class": "media-user-status"})
    if element:
        return element.text.strip()
    return "Неизвестно"

def parse_price(soup):
    """
    парсит цену лотов
    """
    max_price = -1
    max_price_link = None
    
    for element in soup.find_all("a", {"class": 'tc-item'}):
        price_lot = element.find("div", class_="tc-price")
        
        if price_lot and "sort" not in price_lot.get("class", []):
            try:
                price = float(price_lot.get_text(strip=True).replace(' ', '').replace(',', '.').replace('₽', ''))
                
                if price > max_price:
                    max_price = price
                    max_price_link = element.get("href")
            except ValueError:
                logging.warning(f"Некорректное значение цены: {price_lot.get_text(strip=True)}")
    
    return (max_price, max_price_link) if max_price != -1 else "Неизвестно"

def parse_avatar(soup):
    """парс аватара"""
    element = soup.find("div", {"class": "avatar-photo"})
    if element:
        style = element.get("style")
        if style:
            avatar_link = re.search(r"url\((.*?)\)", style).group(1).strip('"')
            return avatar_link

def parse_last_review(soup):
    """парс  ласт отзыва"""
    element = soup.find("div", {"class": "review-container"})
    if element:
        lines = [line.strip() for line in element.text.strip().splitlines() if line.strip()]

        review_date = lines[0] if len(lines) > 0 else ""
        game = lines[1] if len(lines) > 1 else ""
        review = ""

        if len(lines) > 2:
            if any(char.isdigit() for char in lines[2]) or "₽" in lines[2]:
                review = " ".join(lines[3:]).strip() if len(lines) > 3 else ""
            else:
                review = " ".join(lines[2:]).strip()

        return f"Дата написания: {review_date}, Игра и цена: {game}, Отзыв: {review}"

    return "Нет отзывов, , , "

def parse_average_price(soup):
    """парс средней цены (прайс всех лотов / кол-во лотов)"""
    prices_list = []

    for element in soup.find_all("a", {"class": 'tc-item'}):
        price_lot = element.find("div", class_="tc-price")
        
        if price_lot and "sort" not in price_lot.get("class", []):
            try:
                price = float(price_lot.get_text(strip=True).replace(' ', '').replace(',', '.').replace('₽', ''))
                prices_list.append(price)

            except ValueError:
                logging.warning(f"Некорректное значение цены: {price_lot.get_text(strip=True)}")

    if prices_list:
        average_price = sum(prices_list) / len(prices_list)
        average_price = round(average_price, 2)
        logging.info(f"Средняя цена: {average_price:.2f} руб.\n{prices_list}")
        
        return average_price
    else:
        logging.warning("Не найдено цены в разделе.")

def parse_lots4prices(soup):
    """парс лотов с ценами"""
    elements = soup.select("a.tc-item")
    data = []

    for element in elements:
        link = element.get('href')
        if link and "funpay.com/lots/offer?id=" in link:
            lot_id = link.split("funpay.com/lots/offer?id=", 1)[1]
            name_element = element.select_one("div.tc-desc-text")
            price_element = element.select_one("div.tc-price")

            if name_element and price_element:
                name = name_element.text.strip()
                price = price_element.text.strip()
                data.append((lot_id, name, price))

    return data

def save_user_data4file(soup, user_id, new_data): #TODO не обновляет данные (старые -> новые)
    """
    Сохраняет данные пользователя в JSON-файл"""
    try:
        with open(USER_LIST_FILE, "r", encoding="UTF-8") as f:
            data = json.load(f)
            logging.info(f"Чтение данных из {USER_LIST_FILE}")
    except FileNotFoundError:
        data = {}

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if str(user_id) in data:
        logging.info(f"Запись для {user_id} уже существует")
        return

    if user_id not in data:
        logging.info(f"Добавлена новая запись для {user_id}")
        logging.info(f"user_id: {user_id}")
        lots = parse_lots4prices(soup)

        data[user_id] = {
            current_time: new_data,
            "lots": {
                "data": lots
                },
            }
    else:
        logging.info(f"Запись для {user_id} уже существует")
        return

    with open(USER_LIST_FILE, "w", encoding="UTF-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def parse_usr_data(user_id):
    """принт"""
    html_response = fetch_user_data(user_id)
    if html_response is None:
        return
    
    soup = BeautifulSoup(html_response, "lxml")
    
    uz = parse_username(soup)
    reviews = parse_reviews_count(soup)
    estimation = parse_estimation(soup)
    date_reg = parse_registration_date(soup)
    count_offers = parse_offers_count(soup)
    last_review = parse_last_review(soup)
    lots = parse_lot_count(soup)
    status = parse_status(soup)
    price, link = parse_price(soup)
    avr_price = parse_average_price(soup)
    avatar = parse_avatar(soup)
    games = parse_most_popular_game4reviews(soup)

    if len(last_review) >= 80:
        last_review = last_review[:80] + "..."

    data = {
        "username": uz,
        "reviews": reviews,
        "estimation": estimation,
        "date_reg": date_reg,
        "count_offers": count_offers,
        "lots": lots,
        "last_review": last_review,
        "status": status,
        "max_price": f"{price}₽",
        "link": link,
        "avr_price": avr_price,
        "avatar": avatar,
        "bestgames4reviews": games
    }
    table_data = list(data.items())

    table = tabulate(table_data, headers=["Параметр", "Значение"], tablefmt="pretty")
    logging.info(Fore.GREEN + table + Style.RESET_ALL)
    save_user_data4file(soup, user_id, data)

if __name__ == "__main__":
    parse_usr_data(10231791) #СЮДА ВСТАВЛЯТЬ АЙДИ ЮЗЕРА (https://funpay.com/users/10231791/ --> 10231791)
