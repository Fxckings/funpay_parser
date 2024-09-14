import requests
import aiohttp
from bs4 import BeautifulSoup
import logging
from colorama import Fore, Style, init
import re
from collections import Counter
from enums import Data

init()
USER_LIST_FILE = 'userdata.json'

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def fetch_user_data(user_id):
    """
    Функция для получения данных пользователя.
    """
    url = f"https://funpay.com/users/{user_id}/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5), ssl=False) as response:
                response.raise_for_status()
                return await response.read()
    except aiohttp.ClientError as e:
        logging.error(f"Ошибка при запросе данных пользователя: {e}")
        return None


async def parse_reviews_count(soup):
    """
    парсит кол-во отзывов
    """
    for element in soup.find_all(class_=["rating-full-count", "text-mini text-light mb5"]):
        text = element.get_text(strip=True).replace("Всего ", "").replace("отзыв", "").replace('а', '').replace('ов', '')
        if text.isdigit():
            return text
    return "Неизвестно"

async def parse_most_popular_game4reviews(soup):
    """
    самые популярные игры по отзывов #TODO парсит 25 отзывов, а и то меньше, чем надо, фикситб
    """
    games = [element.find("div", {"class": "review-item-detail"}).text.strip().split(",")[0].strip() for element in soup.find_all("div", {"class": "review-item-user"})]
    game_popularity = Counter(games)
    top_games = game_popularity.most_common(3)

    logging.info(f"Получено кол-во отзывов: {Fore.GREEN} {len(games)} {Style.RESET_ALL}")
    return [f"{game[0]} - {game[1]}" for game in top_games]

async def parse_username(soup):
    """
    парсит имя пользователя
    """
    element = soup.select_one(".mr4")
    return element.text.strip() if element else "Неизвестно"

async def parse_estimation(soup):
    """рейтинг"""
    return (soup.select_one(".big") or {}).text.strip() or "Неизвестно"

async def parse_registration_date(soup):
    """дату регестрации"""
    text = next((element.text.split(), ["Неизвестно"])[0] for element in (soup.find("div", {"class": "text-nowrap"}),))
    return ' '.join([text[0], text[1], text[2]])

async def parse_offers_count(soup):
    """
    парсит кол-во предложений (категорий/игр)
    """
    return len(soup.select(".offer")) - 1 #1 offer это отзывы))

async def parse_lot_count(soup):
    """
    парсит кол-во лотов
    """
    return len(soup.select(".tc-item"))

async def parse_status(soup):
    """статус"""
    element = soup.select_one(".media-user-status")
    return element.text.strip() if element else "Неизвестно"

async def parse_price(soup):
    """
    парсит цену лотов
    """
    max_price = -1
    max_price_link = None
    
    for element in soup.find_all("a", class_="tc-item"):
        price_lot = element.find("div", class_="tc-price", recursive=False)
        if price_lot and "sort" not in price_lot.get("class", []):
            try:
                price = float(price_lot.get_text(strip=True).replace(' ', '').replace(',', '.').replace('₽', ''))
                if price > max_price:
                    max_price = price
                    max_price_link = element.get("href")
            except ValueError:
                logging.warning(f"Некорректное значение цены: {price_lot.get_text(strip=True)}")
    
    return (max_price, max_price_link) if max_price != -1 else "Неизвестно"

async def parse_avatar(soup):
    """аватарка"""
    avatar_photo = soup.select_one(".avatar-photo[style]")
    if avatar_photo:
        return re.search(r"url\((.*?)\)", avatar_photo["style"]).group(1).strip('"')

async def parse_last_review(soup):
    """последний отзыв"""
    review_container = soup.find("div", {"class": "review-container"})
    if review_container:
        lines = [line.strip() for line in review_container.text.strip().splitlines() if line.strip()]
        return f"Дата написания: {lines[0]}, Игра и цена: {lines[1]}, Отзыв: {' '.join(lines[2:])}" if len(lines) > 2 else "Нет отзывов"
    return "Не удалось получить данные"

async def parse_average_price(soup):
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
        
        return average_price
    else:
        logging.warning("Не найдено цены в разделе.")

async def mansory_check(soup):
    """парсит есть ли рублевки мансори"""
    async for lot_id, name, price in parse_lots4prices(soup):
        if name.startswith("💎АВТОВЫДАЧА💎 🔥8 Ball Pool: Гайд для новичков🔥") or "💎АВТОВЫДАЧА💎" in name:
            return True
    
    return False

async def parse_lots4prices(soup):
    """парс лотов с ценами"""
    lot_elements = soup.select("a.tc-item[href*='funpay.com/lots/offer?id=']")
    for element in lot_elements[:20]:
        lot_id = element["href"].split("funpay.com/lots/offer?id=", 1)[1]
        name = element.select_one(".tc-desc-text").text.strip()
        price = element.select_one(".tc-price").text.strip()

        yield lot_id, name, price

async def parse_usr_data(user_id):
    """Парсит данные пользователя."""
    html_response = await fetch_user_data(user_id)
    if html_response is None:
        return None
    
    soup = BeautifulSoup(html_response, "html.parser")
    
    data = Data(
        await parse_username(soup),
        await parse_reviews_count(soup),
        await parse_estimation(soup),
        await parse_registration_date(soup),
        await parse_offers_count(soup),
        await parse_last_review(soup),
        await parse_lot_count(soup),
        await parse_status(soup),
        *(await parse_price(soup)),
        await parse_average_price(soup),
        await parse_avatar(soup),
        await parse_most_popular_game4reviews(soup),
        await mansory_check(soup)
    )
    
    return data
