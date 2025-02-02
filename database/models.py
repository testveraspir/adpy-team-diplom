import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship
from typing import List

# Создаем базовый класс для моделей
Base = declarative_base()


class Status(Base):
    """
    Модель статусов отношений между пользователями.
    Например: 'favorite' или 'black list'
    """
    __tablename__ = 'status'

    id = sq.Column(sq.Integer, primary_key=True)
    name = sq.Column(sq.String(length=40), unique=True)

    # Добавляем relationship для удобства работы с зависимыми объектами
    preferences = relationship("Preferences", back_populates="status")

    def __repr__(self):
        return f"Status(id={self.id}, name='{self.name}')"


class User(Base):
    """
    Модель пользователя бота.
    Хранит уникальный идентификатор пользователя из ВКонтакте.
    """
    __tablename__ = 'user'

    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, unique=True)  # Уникальный ID пользователя ВК

    # Добавляем relationship для удобства работы с предпочтениями пользователя
    preferences = relationship("Preferences", back_populates="user")

    def __repr__(self):
        return f"User(id={self.id}, vk_id={self.vk_id})"


class Preferences(Base):
    """
    Модель предпочтений пользователя.
    Хранит информацию о просмотренных анкетах и их статусах (избранное/черный список).
    """
    __tablename__ = 'preferences'

    id = sq.Column(sq.Integer, primary_key=True)
    # ID пользователя, который смотрит анкеты
    vk_id = sq.Column(sq.Integer, sq.ForeignKey('user.vk_id'))
    # ID просмотренной анкеты
    watched_vk_id = sq.Column(sq.Integer)
    # ID статуса отношения (избранное/черный список)
    status_id = sq.Column(sq.Integer, sq.ForeignKey('status.id'))

    # Добавляем связи для удобства работы с объектами
    user = relationship("User", back_populates="preferences")
    status = relationship("Status", back_populates="preferences")

    def __repr__(self):
        return f"Preferences(id={self.id}, vk_id={self.vk_id}, " \
               f"watched_vk_id={self.watched_vk_id}, status_id={self.status_id})"