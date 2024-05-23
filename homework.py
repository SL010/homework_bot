import logging
import os
import sys
import time
from contextlib import suppress
from http import HTTPStatus
# from logging import StreamHandler

import requests
from dotenv import load_dotenv
from telebot import TeleBot, apihelper

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
    tokens = ('PRACTICUM_TOKEN', 'TELEGRAM_CHAT_ID', 'TELEGRAM_TOKEN')
    missing_tokens = [
        token for token in tokens
        if not globals()[token]
    ]
    message_error = f'Отсутствуют ключи доступа {missing_tokens}'
    if len(missing_tokens) != 0:
        logging.critical(message_error)
        sys.exit(message_error)


def send_message(bot, message):
    """Отправляем сообщение в Telegram-чат."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logging.debug('Сообщение отправлено')


def get_api_answer(timestamp):
    """Запрос к эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    try:
        homework = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as error:
        raise ConnectionError(
            f'Возникла ошибка при выполнении запроса: {error}'
        )
    if homework.status_code != HTTPStatus.OK:
        raise ValueError(f'Ошибка ответа сервера {homework.status_code}')
    return homework.json()


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError(
            f'Получен неожиданный тип данных в ответе API {type(response)}'
        )
    if 'homeworks' not in response:
        raise KeyError('Отсутствует ключ "homeworks" в словаре ответа API')

    if not isinstance(response['homeworks'], list):
        raise TypeError('Получен неожиданный тип данных при запросе'
                        'списка домашних работ')


def parse_status(homework):
    """.
    Извлекаем из информации о конкретной
    домашней работе статус этой работы.
    """
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
        if homework_status not in HOMEWORK_VERDICTS:
            raise ValueError(f'Статус {homework_status} недокументирован')
    except KeyError as error:
        raise KeyError(f'Отсутствует ключ словаря: {error}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    # logger = logging.getLogger(__name__)
    # file_handler = logging.FileHandler('log_file.log')
    # formatter = logging.Formatter('%(asctime)s - %(name)s -
    # %(levelname)s - %(message)s')
    # file_handler.setFormatter(formatter)
    # logger.setLevel(logging.DEBUG)
    # stream_handler = StreamHandler()
    # logger.addHandler(stream_handler)
    # logger.handlers[0].stream = sys.stdout

    check_tokens()
    # Создаем объект класса бота
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    # timestamp = 1549962000
    previos_message = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homework = response['homeworks'][0]
            if not homework:
                logging.debug('Отсутствует изменение статуса')
                continue
            new_status = parse_status(homework)
            if new_status != previos_message:
                send_message(bot, new_status)
                previos_message = new_status
                timestamp = response.get('current_date', timestamp)
            else:
                logging.debug('Статус не изменился, сообщение не отправлено')
        except apihelper.ApiException as error:
            logging.error(f'Сбой отправки сообщения: {error}', exc_info=True)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(f'Сбой в работе программы: {error}', exc_info=True)
            with suppress(apihelper.ApiException):
                with suppress(apihelper.ApiException):
                    send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG,
        handlers=[
            logging.FileHandler("log_file.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    main()
