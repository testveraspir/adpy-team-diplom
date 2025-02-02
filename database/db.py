# Импорт необходимых библиотек
from sqlalchemy.orm import sessionmaker, Query
import sqlalchemy as sq
from typing import List, Optional, Type
import database.models
from database.models import User, Status, Preferences
from dotenv import load_dotenv
import os

# Загрузка переменных окружения из файла .env
load_dotenv()


class DB:
    """
    Класс для работы с базой данных.
    Обеспечивает подключение к БД и основные операции с данными.
    """

    def __init__(self):
        """
        Инициализация подключения к базе данных.
        - Создаёт движок SQLAlchemy
        - Настраивает сессию для работы с БД
        """
        self.Base = database.models.Base
        # Создаем движок SQLAlchemy, используя параметры из .env файла
        self.engine = sq.create_engine(os.getenv('DSN'))
        # Создаем фабрику сессий
        self.Session = sessionmaker(bind=self.engine)
        # Создаем экземпляр сессии
        self.session = self.Session()

    def drop_tables(self) -> None:
        """Удаляет все таблицы из базы данных"""
        self.Base.metadata.drop_all(self.engine)

    def create_tables(self) -> None:
        """Создает все таблицы в базе данных на основе моделей"""
        self.Base.metadata.create_all(self.engine)

    def status_filler(self) -> None:
        """
        Заполняет таблицу статусов начальными значениями:
        - favorite (избранное)
        - black list (черный список)
        """
        existing_statuses = self.session.query(Status).all()
        if not existing_statuses:  # Если статусов нет, добавляем их
            try:
                self.session.add(Status(name='favorite'))
                self.session.add(Status(name='black list'))
                self.session.commit()
                print("Статусы успешно добавлены")
            except Exception as e:
                print(f"Ошибка при добавлении статусов: {e}")
                self.session.rollback()

    def check_user(self, self_id: int) -> None:
        """
        Проверяет существование пользователя в БД.
        Если пользователь не найден - создает его.

        Args:
            self_id (int): ID пользователя ВКонтакте
        """
        user = self.session.query(User).filter_by(vk_id=self_id).first()
        if not user:
            self.session.add(User(vk_id=self_id))
            self.session.commit()

    def request_preferences(self, self_id: int, user_id: int) -> list[Type[Preferences]]:
        """
        Получает все предпочтения пользователя относительно просмотренного профиля.

        Args:
            self_id (int): ID пользователя ВКонтакте, который смотрит анкеты
            user_id (int): ID просмотренного пользователя

        Returns:
            List[Preferences]: Список объектов предпочтений
        """
        return self.session.query(Preferences).filter_by(
            vk_id=self_id,
            watched_vk_id=user_id
        ).all()

    def add_favorite(self, self_id: int, user_id: int) -> None:
        """
        Добавляет пользователя в избранное.

        Args:
            self_id (int): ID пользователя ВКонтакте
            user_id (int): ID пользователя для добавления в избранное
        """
        self.session.add(Preferences(
            vk_id=self_id,
            watched_vk_id=user_id,
            status_id=1  # 1 = favorite status
        ))
        self.session.commit()

    def add_blacklist(self, self_id: int, user_id: int) -> None:
        """
        Добавляет пользователя в черный список.

        Args:
            self_id (int): ID пользователя ВКонтакте
            user_id (int): ID пользователя для добавления в черный список
        """
        self.session.add(Preferences(
            vk_id=self_id,
            watched_vk_id=user_id,
            status_id=2  # 2 = black list status
        ))
        self.session.commit()

    def request_favorite_list(self, self_id: int) -> list[Type[Preferences]]:
        """
        Получает список избранных пользователей.

        Args:
            self_id (int): ID пользователя ВКонтакте

        Returns:
            List[Preferences]: Список объектов предпочтений со статусом 'favorite'
        """
        return self.session.query(Preferences).filter_by(
            vk_id=self_id,
            status_id=1  # 1 = favorite status
        ).all()

    def __del__(self):
        """Закрывает сессию при уничтожении объекта"""
        self.session.close()