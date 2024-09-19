import aiohttp
from bs4 import BeautifulSoup
from loguru import logger
import re
from collections import Counter
from enums.enums import Data
import asyncio
import random

logger.add("tgbot.log", format="{time} | {level} | {message}", level="INFO")

class Parser:
    def __init__(self):
        pass

    async def fetch_user_data(self, user_id):
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
            logger.error(f"Ошибка при запросе данных пользователя: {e}")
            return None


    async def parse_reviews_count(self, soup):
        """
        парсит кол-во отзывов
        """
        for element in soup.find_all(class_=["rating-full-count", "text-mini text-light mb5"]):
            text = element.get_text(strip=True).replace("Всего ", "").replace("отзыв", "").replace('а', '').replace('ов', '')
            if text.isdigit():
                return text
        return "Неизвестно"

    async def parse_most_popular_game4reviews(self, soup):
        """
        самые популярные игры по отзывов #TODO парсит 25 отзывов, а и то меньше, чем надо, фикситб
        """
        games = [element.find("div", {"class": "review-item-detail"}).text.strip().split(",")[0].strip() for element in soup.find_all("div", {"class": "review-item-user"})]
        game_popularity = Counter(games)
        top_games = game_popularity.most_common(3)

        return '\n'.join([f"{game[0]} - {game[1]}" for game in top_games])

    async def parse_username(self, soup):
        """
        парсит имя пользователя
        """
        element = soup.select_one(".mr4")
        return element.text.strip() if element else "Неизвестно"

    async def parse_estimation(self, soup):
        """рейтинг"""
        element = soup.select_one(".big")
        return element.text.strip() if element else "Неизвестно"

    async def parse_registration_date(self, soup):
        """дату регестрации"""
        text = next((element.text.split(), ["Неизвестно"])[0] for element in (soup.find("div", {"class": "text-nowrap"}),))
        return ' '.join([text[0], text[1], text[2]])

    async def parse_offers_count(self, soup):
        """
        парсит кол-во предложений (категорий/игр)
        """
        return len(soup.select(".offer")) - 1 #1 offer это отзывы))

    async def parse_lot_count(self, soup):
        """
        парсит кол-во лотов
        """
        return len(soup.select(".tc-item"))

    async def parse_status(self, soup):
        """статус"""
        element = soup.select_one(".media-user-status")
        return element.text.strip() if element else "Неизвестно"

    async def parse_price(self, soup):
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
                    logger.warning(f"Некорректное значение цены: {price_lot.get_text(strip=True)}")
        
        return (max_price, max_price_link) if max_price != -1 else "Неизвестно"

    async def parse_avatar(self, soup):
        """аватарка"""
        avatar_photo = soup.select_one(".avatar-photo[style]")
        if avatar_photo:
            return re.search(r"url\((.*?)\)", avatar_photo["style"]).group(1).strip('"')

    async def parse_last_review(self, soup):
        """последний отзыв"""
        review_container = soup.find("div", {"class": "review-container"})
        if review_container:
            lines = [line.strip() for line in review_container.text.strip().splitlines() if line.strip()]
            return f"Дата написания: {lines[0]}, Игра и цена: {lines[1]}, Отзыв: {' '.join(lines[2:])}" if len(lines) > 2 else "Нет отзывов"
        return "Не удалось получить данные"

    async def parse_average_price(self, soup):
        """парс средней цены (прайс всех лотов / кол-во лотов)"""
        prices_list = []

        for element in soup.find_all("a", {"class": 'tc-item'}):
            price_lot = element.find("div", class_="tc-price")
            
            if price_lot and "sort" not in price_lot.get("class", []):
                try:
                    price = float(price_lot.get_text(strip=True).replace(' ', '').replace(',', '.').replace('₽', ''))
                    prices_list.append(price)

                except ValueError:
                    logger.warning(f"Некорректное значение цены: {price_lot.get_text(strip=True)}")

        if prices_list:
            average_price = sum(prices_list) / len(prices_list)
            average_price = round(average_price, 2)
            
            return average_price
        else:
            logger.warning("Не найдено цены в разделе.")

    async def parse_auto_lots(self, soup):
        """парс лотов с автовыдачей"""
        return len(soup.select(".sc-offer-icons"))

    async def mansory_check(self, soup):
        """парсит есть ли рублевки мансори"""
        async for lot_id, name, price in self.parse_lots4prices(soup):
            if name.startswith("💎АВТОВЫДАЧА💎 🔥8 Ball Pool: Гайд для новичков🔥") or "💎АВТОВЫДАЧА💎" in name:
                return True
        
        return False

    async def parse_lots4prices(self, soup):
        """парс лотов с ценами"""
        lot_elements = soup.select("a.tc-item[href*='funpay.com/lots/offer?id=']")
        for element in lot_elements[:20]:
            lot_id = element["href"].split("funpay.com/lots/offer?id=", 1)[1]
            name = element.select_one(".tc-desc-text").text.strip()
            price = element.select_one(".tc-price").text.strip()

            yield lot_id, name, price

    async def check_banned(self, soup):
        """парсит забанен ли юзер"""
        banned_element = soup.select_one(".user-badges")
        if banned_element and banned_element.text == "заблокирован":
            return True

        return False

    async def fetch_lot_data(self, session, lot_url):
            """Запрос данных по лоту и извлечение информации"""
            try:
                async with session.get(lot_url, ssl=False) as response:
                    response.raise_for_status()
                    html_response = await response.text()

                soup = BeautifulSoup(html_response, "html.parser")
                cat_name = soup.find("span", class_="inside").text
                stars = soup.find("span", class_="big").text

                logger.info(type(stars))
                logger.info(f"Stars: {stars} Category: {cat_name}")
                if '.' in stars:
                    logger.info("returning" )
                    return

                # Возвращаем только если звёзд меньше 5
                if int(stars) < 5:
                    logger.info(f"Stars: {stars} Category: {cat_name} ening")
                    return [stars, cat_name]
            except Exception as e:
                logger.error(f"Error fetching {lot_url}: {e}")
            return None
        
    async def parse_category(self, session, category):
        """Парсинг категории для извлечения ссылки на первый лот и его обработка"""
        try:
            lot_in_category = category.find("a", class_="tc-item")
            if lot_in_category:
                link_to_lot = lot_in_category.get("href")
                return await self.fetch_lot_data(session, link_to_lot)
        except Exception as e:
            logger.error(f"Error parsing category: {e}")
        return None
    
    async def sanction_check(self, soup):
        """Парсит количество звезд в категориях и возвращает список"""
        lst = []
        categories = soup.find_all("div", class_="offer")
        # Если категорий более 30, удаляем случайные категории

        if len(categories) > 30:
            random_categories = random.sample(categories, 30)
            categories = random_categories

        # Создаём сессию и выполняем запросы параллельно
        async with aiohttp.ClientSession() as session:
            tasks = [self.parse_category(session, category) for category in categories]
            results = await asyncio.gather(*tasks)

        # Фильтруем результаты, чтобы добавить только те, где есть данные
        lst = [result for result in results if result]
        return lst

    async def parse_usr_data(self, user_id, lazy=False):
        html_response = await self.fetch_user_data(user_id)
        if html_response is None:
            return None
        
        soup = BeautifulSoup(html_response, "html.parser")
        ban = await self.check_banned(soup)
        if ban:
            return None
        
        if lazy:
            # Ленивая загрузка только минимальных данных
            data = Data(
                await self.parse_username(soup),
                await self.parse_reviews_count(soup),
                await self.parse_estimation(soup),
                await self.parse_status(soup),
                None, None, None, None, None, None, None, None, None, f"https://funpay.com/users/{user_id}/"
            )
        else:
            # Полная загрузка данных
            data = Data(
                await self.parse_username(soup),
                await self.parse_reviews_count(soup),
                await self.parse_estimation(soup),
                await self.parse_registration_date(soup),
                await self.parse_offers_count(soup),
                await self.parse_last_review(soup),
                await self.parse_lot_count(soup),   
                await self.parse_status(soup),
                *(await self.parse_price(soup)),
                await self.parse_average_price(soup),
                await self.parse_avatar(soup),
                await self.parse_most_popular_game4reviews(soup),
                await self.mansory_check(soup),
                await self.parse_auto_lots(soup),
                f"https://funpay.com/users/{user_id}/",
                await self.sanction_check(soup)
            )
            
        return data