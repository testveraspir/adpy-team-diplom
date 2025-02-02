import vk_api
from vk_api.bot_longpoll import VkBotLongPoll
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import datetime
from dotenv import load_dotenv
import os

load_dotenv()


class VK:
    def __init__(self):
        self.vk_group_session = vk_api.VkApi(token=os.getenv('GROUP_TOKEN'))
        self.vk_user_session = vk_api.VkApi(token=os.getenv('USER_TOKEN'))
        self.vk_group = self.vk_group_session.get_api()
        self.vk_user = self.vk_user_session.get_api()
        self.longpoll = VkBotLongPoll(self.vk_group_session, group_id=os.getenv('GROUP_ID'))

    def search(self, sex, city, age, count=1000, step=-3):
        """
        Поиск пользователей с учетом заданных критериев
        """
        first_search = []
        opposite_sex = 1 if int(sex) == 2 else 2  # 1 - женский, 2 - мужской

        for age_differ in range(step, -step + 1):
            try:
                search_result = self.vk_user.users.search(
                    count=count,
                    sex=opposite_sex,
                    city=city,
                    age_from=18,
                    age_to=100,
                    has_photo='1',
                    status='6',
                    fields="city, bdate, sex, can_write_private_message"
                )
                first_search.extend(search_result['items'])
            except vk_api.exceptions.ApiError as e:
                print(f"Ошибка при поиске: {e}")
                continue

        # Фильтруем результаты
        user_list = []
        for user in first_search:
            if (not user['is_closed'] and
                    'city' in user and
                    str(user['city']['id']) == str(city) and
                    user.get('can_write_private_message', 1)):
                if 'bdate' in user:
                    try:
                        bdate = datetime.datetime.strptime(user['bdate'], '%d.%m.%Y')
                        user_age = (datetime.datetime.now() - bdate).days // 365
                        if user_age >= 18:
                            user_list.append(user)
                    except ValueError:
                        continue
                else:
                    user_list.append(user)

        return user_list

    def preview_photos(self, user_photo_list: dict) -> list:
        """
        Получение топ-3 фотографий по количеству лайков
        """
        preview_photo_list = []
        for photo in user_photo_list["items"]:
            try:
                preview_photo_list.append({
                    'photo_id': photo['id'],
                    'likes': photo['likes']['count'],
                    'photo_link': max(photo['sizes'], key=lambda x: x['height'])['url']
                })
            except (KeyError, ValueError) as e:
                print(f"Ошибка обработки фото: {e}")
                continue

        preview_photo_list.sort(key=lambda x: x['likes'], reverse=True)
        top_photos = preview_photo_list[:3]
        return [[photo['photo_id'], photo['likes'], photo['photo_link']] for photo in top_photos]

    def get_photo(self, found_user_id: int) -> dict:
        """
        Получение фотографий пользователя
        """
        try:
            return self.vk_user.photos.get(
                owner_id=found_user_id,
                album_id="profile",
                extended=1
            )
        except vk_api.exceptions.ApiError as e:
            print(f"Ошибка получения фото: {e}")
            return {"items": []}

    def send_message(self, session, vk_id: int, text: str, attachment=None, keyboard=None) -> None:
        """
        Отправка сообщения пользователю
        """
        try:
            session.method('messages.send', {
                'user_id': vk_id,
                'message': text,
                'random_id': 0,
                'keyboard': keyboard,
                'attachment': attachment
            })
        except vk_api.exceptions.ApiError as e:
            print(f"Ошибка отправки сообщения: {e}")

    def profile_info(self, vkinder_user_id: int) -> dict:
        """
        Получение информации о профиле пользователя
        """
        try:
            user = self.vk_group_session.method('users.get', {
                'user_ids': vkinder_user_id,
                'fields': 'sex, bdate, city, relation'
            })[0]

            name = f"{user['first_name']} {user['last_name']}"
            sex = user['sex']

            age = ''
            if 'bdate' in user:
                try:
                    bdate = datetime.datetime.strptime(user['bdate'], '%d.%m.%Y')
                    age = str((datetime.datetime.now() - bdate).days // 365)
                except ValueError:
                    age = ''

            city = user['city']['id'] if 'city' in user else ''
            city_title = user['city']['title'] if 'city' in user else ''

            return {
                'name': name,
                'sex': str(sex),
                'age': age,
                'city': str(city),
                'city_title': city_title
            }
        except Exception as e:
            print(f"Ошибка получения профиля: {e}")
            return {
                'name': '',
                'sex': '',
                'age': '',
                'city': '',
                'city_title': ''
            }

    def keyboard(self):
        """
        Создание клавиатур для бота
        """
        welcome_keyboard = VkKeyboard(one_time=True)
        welcome_keyboard.add_button("Начать", color=VkKeyboardColor.POSITIVE)
        welcome_keyboard.add_button("Мои данные", color=VkKeyboardColor.POSITIVE)

        regular_keyboard = VkKeyboard()
        regular_keyboard.add_button("Дальше", color=VkKeyboardColor.POSITIVE)
        regular_keyboard.add_button("В избранное", color=VkKeyboardColor.POSITIVE)
        regular_keyboard.add_button("В ЧС", color=VkKeyboardColor.NEGATIVE)
        regular_keyboard.add_line()
        regular_keyboard.add_button("Моё избранное", color=VkKeyboardColor.SECONDARY)

        back_keyboard = VkKeyboard()
        back_keyboard.add_button("Дальше", color=VkKeyboardColor.POSITIVE)

        return welcome_keyboard, regular_keyboard, back_keyboard