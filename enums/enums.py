class Data:
    def __init__(self, username: str, reviews: str, estimation: str, date_reg: str, count_offers: str, last_review: str, lots: str, status: str, max_price: str, link_to_max_price: str, average_price: str, avatar_link: str, games_in_reviews: str, havemansory: bool, autolots: int, userlink: str, sanclist: list):
        self.username = username
        """Имя пользователя, например Tinkovof"""
        self.reviews_count = reviews
        """Кол-во отзывов у пользователя, например 1070"""
        self.estimation = estimation
        """Рейтинг пользователя, например 4.5"""
        self.date_reg = date_reg
        """Дата регистрации пользователя, например 14 мая 2018, 21:03 6 лет назад"""
        self.count_offers = count_offers
        """Кол-вот предложений (категорий) пользователя, не тоже самое что и лоты"""
        self.last_review = last_review
        """Последний отзыв пользователя, формат: В этом месяце Brawl Stars, 10 ₽ 👍 Ответ продавца"""
        self.lots = lots
        """Кол-во лотов у пользователя, например 1602"""
        self.status = status
        """Статус, например "онлайн" """
        self.max_price = max_price
        """Самый дорогий лот пользователя"""
        self.link_to_max_price = link_to_max_price
        """Ссылка на самый дорогой лот пользователя"""
        self.average_price = average_price
        """Средняя цена лотов пользователя, по формуле (кол-во лотов) / их цену вместе"""
        self.avatar_link = avatar_link
        """Ссылка на аватар юзера"""
        self.games_in_reviews = games_in_reviews
        """Популярные игры в отзывах"""
        self.havemansory = havemansory
        """Есть ли рублевки мансори в лотах?"""
        self.autolots = autolots
        """Кол-во лотов с автовыдачей"""
        self.userlink = userlink
        """Ссылка на профиль пользователя"""
        self.sanclist = sanclist
        """Ограничения рейтинга пользователя, основа на 30-50 категориях, так-как больше будет ошибка"""