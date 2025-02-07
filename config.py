from dotenv import load_dotenv
import os

# Загрузка переменных окружения из файла .env
dotenv_path = 'config_example.env'
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
GROUP_TOKEN = os.getenv('GROUP_TOKEN')
USER_TOKEN = os.getenv('USER_TOKEN')
GROUP_ID = os.getenv('GROUP_ID')
login = os.getenv('LOGIN')
password_psq = os.getenv('PASSWORD_PSQ')
name_db = os.getenv('NAME_DB')
