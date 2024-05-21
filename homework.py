from telebot import TeleBot
import requests
import os
import logging
import time
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка доступности переменных окружения."""
    if not all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        logging.critical('Осутствуют ключи доступа')
        raise SystemExit


def send_message(bot, message):
    """Отправляем сообщение в Telegram-чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение отправлено')
    except Exception as error:
        logging.error(f'Сбой отправки сообщения: {error}')


def get_api_answer(timestamp):
    """Запрос к эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    try:
        homework = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as error:
        logging.error(f'Сбой в работе программы: {error}')
    if homework.status_code != 200:
        raise Exception
    return homework.json()


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('не список')
    if 'homeworks' not in response:
        raise KeyError('Отсутствует ключ в словаре')

    if not isinstance(response['homeworks'], list):
        raise TypeError('не список')

    if len(response['homeworks']) == 0:
        logging.debug('Отсутствие изменение статуса')
        return None
    else:
        return response['homeworks'][0]


def parse_status(homework):
    """.
    Извлекаем из информации о конкретной
    домашней работе статус этой работы.
    """
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
        if homework_status not in HOMEWORK_VERDICTS:
            raise Exception
    except KeyError as error:
        logging.error(f'Отсутствует ключ в словаре: {error}')
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        filemode='w',
    )

    # Создаем объект класса бота
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    current_status = ''
    while True:
        check_tokens()
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            new_status = parse_status(homework)
            if new_status != current_status:
                send_message(bot, new_status)
                current_status = new_status
                timestamp = response.get('timestamp')
            else:
                logging.error('ошибка отправки сообщения')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(f'Сбой в работе программы: {error}')
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
