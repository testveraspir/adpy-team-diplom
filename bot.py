from vk_api.bot_longpoll import VkBotEventType
from database.db import DB
from api import VK  # Исправленный импорт
from threading import Thread
from datetime import datetime
import random
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='vtinder.log'
)
logger = logging.getLogger(__name__)


class VTinderBot:
    def __init__(self):
        """Инициализация бота"""
        self.vk = VK()
        self.db = DB()
        # Словарь для хранения состояний пользователей
        self.user_dict = {}

    def get_user_age(self, self_id):
        """Запрашивает возраст у пользователя"""
        self.vk.send_message(
            self.vk.vk_group_session,
            self_id,
            "Не могу понять, сколько тебе лет, напиши для более точного подбора."
        )

        for event in self.vk.longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                if self_id == event.obj.message["from_id"]:
                    age = event.obj.message["text"]
                    if age.isdigit() and 18 <= int(age) <= 100:
                        return int(age)
                    else:
                        self.vk.send_message(
                            self.vk.vk_group_session,
                            self_id,
                            "Пожалуйста, введите корректный возраст (от 18 до 100)"
                        )

    def show_favorites(self, self_id):
        """Показывает избранные анкеты"""
        try:
            favorites = self.db.request_favorite_list(self_id)
            back_keyboard = self.vk.keyboard()[2]

            if not favorites:
                self.vk.send_message(
                    self.vk.vk_group_session,
                    self_id,
                    "У вас пока нет избранных анкет",
                    keyboard=back_keyboard.get_keyboard()
                )
                return

            for favorite in favorites:
                try:
                    # Получаем данные пользователя
                    user_data = self.vk.vk_user.users.get(
                        user_id=favorite.watched_vk_id,
                        fields="first_name, last_name"
                    )[0]

                    # Получаем фотографии
                    photos = self.vk.get_photo(favorite.watched_vk_id)
                    if photos['count'] > 2:
                        top_photos = self.vk.preview_photos(photos)
                        attachment = (f'photo{favorite.watched_vk_id}_{top_photos[0][0]},'
                                      f'photo{favorite.watched_vk_id}_{top_photos[1][0]},'
                                      f'photo{favorite.watched_vk_id}_{top_photos[2][0]}')

                        self.vk.send_message(
                            self.vk.vk_group_session,
                            self_id,
                            f'{user_data["first_name"]} {user_data["last_name"]}\n'
                            f'https://vk.com/id{favorite.watched_vk_id}\n',
                            attachment,
                            keyboard=back_keyboard.get_keyboard()
                        )
                except Exception as e:
                    logger.error(f"Ошибка при показе избранного профиля: {e}")
                    continue

        except Exception as e:
            logger.error(f"Ошибка при показе избранных: {e}")
            self.vk.send_message(
                self.vk.vk_group_session,
                self_id,
                "Произошла ошибка при показе избранных анкет"
            )

    def search_users(self, self_id):
        """Основная функция поиска и показа анкет"""
        try:
            # Проверяем пользователя в БД
            self.db.check_user(self_id)

            # Получаем информацию о пользователе
            user_info = self.vk.profile_info(self_id)
            city = user_info['city']
            sex = user_info['sex']
            age = user_info['age']

            # Получаем клавиатуры
            keyboards = self.vk.keyboard()
            regular_keyboard = keyboards[1]
            welcome_keyboard = keyboards[0]

            # Если возраст не указан, запрашиваем его
            if not age:
                age = self.get_user_age(self_id)
                if not age:
                    return

            # Ищем подходящих пользователей
            users = self.vk.search(sex, city, age, count=100)
            if not users:
                self.vk.send_message(
                    self.vk.vk_group_session,
                    self_id,
                    "К сожалению, не удалось найти подходящие анкеты. "
                    "Попробуйте изменить критерии поиска.",
                    keyboard=welcome_keyboard.get_keyboard()
                )
                self.user_dict[self_id] = 1
                return

            # Перемешиваем список пользователей
            random.shuffle(users)

            # Показываем анкеты
            for user in users:
                # Проверяем, не остановил ли пользователь поиск
                if self.user_dict[self_id] != 2:
                    break

                # Пропускаем уже просмотренные анкеты
                if self.db.request_preferences(self_id, user["id"]):
                    continue

                try:
                    # Получаем фотографии пользователя
                    photos = self.vk.get_photo(user["id"])
                    if photos['count'] <= 2:
                        continue

                    # Получаем топ-3 фото
                    top_photos = self.vk.preview_photos(photos)
                    attachment = (f'photo{user["id"]}_{top_photos[0][0]},'
                                  f'photo{user["id"]}_{top_photos[1][0]},'
                                  f'photo{user["id"]}_{top_photos[2][0]}')

                    # Отправляем анкету пользователю
                    self.vk.send_message(
                        self.vk.vk_group_session,
                        self_id,
                        f'{user["first_name"]} {user["last_name"]}\n'
                        f'https://vk.com/id{user["id"]}\n',
                        attachment,
                        keyboard=regular_keyboard.get_keyboard()
                    )

                    # Ждем реакции пользователя
                    for event in self.vk.longpoll.listen():
                        if event.type == VkBotEventType.MESSAGE_NEW:
                            if self_id == event.obj.message["from_id"]:
                                command = event.obj.message["text"].lower()

                                if command == "дальше":
                                    break

                                elif command == "в избранное":
                                    self.db.add_favorite(self_id, user["id"])
                                    self.vk.send_message(
                                        self.vk.vk_group_session,
                                        self_id,
                                        f"{user['first_name']} {user['last_name']} добавлен(а) в избранное"
                                    )
                                    break

                                elif command == "в чс":
                                    self.db.add_blacklist(self_id, user["id"])
                                    self.vk.send_message(
                                        self.vk.vk_group_session,
                                        self_id,
                                        f"{user['first_name']} {user['last_name']} добавлен(а) в ЧС"
                                    )
                                    break

                                elif command == "моё избранное":
                                    self.show_favorites(self_id)
                                    continue

                                elif command == "выход":
                                    self.user_dict[self_id] = 1
                                    self.vk.send_message(
                                        self.vk.vk_group_session,
                                        self_id,
                                        "Поиск остановлен",
                                        keyboard=welcome_keyboard.get_keyboard()
                                    )
                                    return

                except Exception as e:
                    logger.error(f"Ошибка при обработке анкеты: {e}")
                    continue

        except Exception as e:
            logger.error(f"Ошибка в поиске пользователей: {e}")
            self.vk.send_message(
                self.vk.vk_group_session,
                self_id,
                "Произошла ошибка при поиске анкет"
            )

    def run(self):
        """Запуск бота"""
        # Инициализация базы данных
        self.db.create_tables()
        self.db.status_filler()

        print("Бот запущен...")
        logger.info("Бот запущен")

        # Получаем клавиатуру приветствия
        welcome_keyboard = self.vk.keyboard()[0]

        try:
            # Основной цикл бота
            for event in self.vk.longpoll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    self_id = event.obj.message["from_id"]
                    message = event.obj.message["text"].lower()

                    # Новый пользователь
                    if self_id not in self.user_dict:
                        self.vk.send_message(
                            self.vk.vk_group_session,
                            self_id,
                            "Привет! Для начала работы нажмите 'Начать'",
                            keyboard=welcome_keyboard.get_keyboard()
                        )
                        self.user_dict[self_id] = 1

                    # Обработка команд
                    elif message == "мои данные" and self.user_dict[self_id] == 1:
                        self.vk.send_message(
                            self.vk.vk_group_session,
                            self_id,
                            f"Ваш ID: {self_id}",
                            keyboard=welcome_keyboard.get_keyboard()
                        )

                    elif message == "начать" and self.user_dict[self_id] == 1:
                        self.user_dict[self_id] = 2
                        self.vk.send_message(
                            self.vk.vk_group_session,
                            self_id,
                            "Начинаем поиск..."
                        )
                        # Запускаем поиск в отдельном потоке
                        search_thread = Thread(target=self.search_users, args=(self_id,))
                        search_thread.start()

        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            raise

        finally:
            logger.info("Бот остановлен")


if __name__ == "__main__":
    bot = VTinderBot()
    try:
        bot.run()
    except KeyboardInterrupt:
        print("Бот остановлен пользователем")
        logger.info("Бот остановлен пользователем")