# homework_bot
python telegram bot
Отслеживает изменения через внешний API и информирует пользователя путем отправки сообщения.

# Технологии:
Python 3.9
python-dotenv 0.20.0
pyTelegramBotAPI 4.14.17

# Как запустить проект:
Клонировать репозиторий и перейти в него в командной строке:

git clone git@github.com:https://github.com/SL010/homework_bot
cd homework_bot
Cоздать и активировать виртуальное окружение:
python -m venv venv
source venv/bin/activate

Установить зависимости из файла requirements.txt:
python -m pip install --upgrade pip
pip install -r requirements.txt

Создать файл .env и записать в переменные окружения необходимые ключи:
  токен профиля на отслеживаемом сервисе
  токен телеграм-бота
  свой ID в телеграме

# Запустить проект:
python homework.py
