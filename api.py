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
        first_search = []
        for age_differ in range(step, -step + 1):
            first_search.extend(self.vk_user.users.search(count=count, sex='1' if sex == '2' else '2',
                                                          city=city,
                                                          age_from=str(int(age) + age_differ),
                                                          age_to=str(int(age) + age_differ), has_photo='1',
                                                          status='6', fields="city, bdate, sex")['items'])

        user_list = [user for user in [user for user in first_search if user['is_closed'] is False and 'city' in user]
                     if str(user['city']['id']) == city]
        return user_list

    def preview_photos(self, user_photo_list: dict) -> list:
        preview_photo_list = [
            {'photo_id': photo['id'], 'likes': photo['likes']['count'],
             'photo_link': [sizes['url'] for sizes in photo['sizes']][-1]}
            for photo in user_photo_list["items"]]
        preview_photo_list.sort(key=lambda dictionary: dictionary['likes'])
        link_list = [[link['photo_id'], link['likes'], link['photo_link']] for link in preview_photo_list[-3:]]
        return link_list

    def get_photo(self, found_user_id: int) -> list:
        photo_list = self.vk_user.photos.get(owner_id=found_user_id, album_id="profile", extended=1)
        return photo_list

    def send_message(self, session, vk_id: int, text: str, attachment=None, keyboard=None) -> None:
        session.method('messages.send',
                       {'user_id': vk_id, 'message': text, 'random_id': 0, 'keyboard': keyboard,
                        'attachment': attachment})

    def profile_info(self, vkinder_user_id: int) -> dict:
        user = self.vk_group_session.method('users.get', {'user_ids': vkinder_user_id,
                                                          'fields': 'sex, bdate, city, relation'})
        name = f'{user[0]["first_name"]} {user[0]["last_name"]}'
        sex = user[0]['sex']
        if 'bdate' in user[0]:
            if len(user[0]['bdate'].split('.')) == 3:
                age = datetime.date.today().year - int(user[0]['bdate'].split('.')[-1])
            else:
                age = ''
        else:
            age = ''
        city = user[0]['city']['id'] if 'city' in user[0] else ''
        city_title = user[0]['city']['title'] if 'city' in user[0] else ''
        return {'name': name, 'sex': str(sex), 'age': str(age), 'city': str(city),
                'city_title': city_title}

    def keyboard(self):
        welcome_keyboard = VkKeyboard(one_time=True)
        regular_keyboard = VkKeyboard()
        welcome_keyboard.add_button(label="Начать", color=VkKeyboardColor.POSITIVE)
        welcome_keyboard.add_button(label="Мои данные", color=VkKeyboardColor.POSITIVE)
        regular_keyboard.add_button(label="Дальше", color=VkKeyboardColor.POSITIVE)
        regular_keyboard.add_button(label="В избранное", color=VkKeyboardColor.POSITIVE)
        regular_keyboard.add_button(label="В ЧС", color=VkKeyboardColor.NEGATIVE)
        regular_keyboard.add_line()
        regular_keyboard.add_button(label="Моё избранное", color=VkKeyboardColor.SECONDARY)
        back_keyboard = VkKeyboard()
        back_keyboard.add_button(label="Дальше", color=VkKeyboardColor.POSITIVE)
        return welcome_keyboard, regular_keyboard, back_keyboard