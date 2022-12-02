import csv
import json
import os
import os.path
import re
from time import sleep
from datetime import datetime

import requests

DATA_WATER_RAW = 'water_data.html'  # данные со всеми наблюдениями
DATA_POSTS_RAW = 'water_posts_data.json'  # словарь id_поста: локация_поста
DATA_WATER_LEVEL = 'water_level.csv'  # датасет с данными наблюдений
DATA_WEATHER = 'weather.csv'  # датасет с погодой за 2008-2017
# список с мин-макс данными для нормализации
DATA_NORMALIZATION = 'normalization_info.json'

DATA_PROCESSED_TRAIN = 'train_data.csv'  # готовый датасет для обучения модели

# словарь id_поста: локация_поста, название_города, id_гисметео,
# резерв_id_гисметео, страница_вики
DATA_POSTS_FULL_RAW = 'posts_fulldata.json'

XGBOOST_MODEL = 'xgboost_model.json'

# для получения данных к некоторым сайтам (gismeteo) нужно имитировать браузер
DEFAULT_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                'AppleWebKit/537.36 (KHTML, like Gecko) '
                                'Chrome/102.0.5005.63 Safari/537.36'}
START_YEAR = 2008
END_YEAR = 2017
WAIT_SLEEP_TIME = 2


def format_data(year, month, day):
    return f'{year}-{month:02d}-{day:02d}'


# requests methods
def get_url(url, params=None, cookies=None):
    r = requests.get(url, params=params, cookies=cookies,
                     headers=DEFAULT_HEADER)
    r.raise_for_status()
    sleep(WAIT_SLEEP_TIME)  # ждём, чтобы не перегрузить сайт запросами

    return r


def post_url(url, data=None, cookies=None, allow_redirects=True):
    r = requests.post(url, data=data, cookies=cookies,
                      allow_redirects=allow_redirects, headers=DEFAULT_HEADER)
    r.raise_for_status()
    sleep(1)  # ждём, чтобы не перегрузить сайт запросами

    return r


# file methods
def get_filepath(file_name, is_raw):
    file_name = re.sub(r'[^\wА-Яа-яёЁ_.)( -\\/]', '', file_name)  # чистка имени
    result = os.path.join(os.getcwd(), 'data')
    if is_raw:
        return os.path.join(result, 'raw', file_name)
    return os.path.join(result, 'processed', file_name)


def is_data_exists(file_name, is_raw=True):
    """ Проверка наличия файла с данными

    :param file_name: название файла с данными
    :param is_raw: сырые ли данные? если да - смотреть в папке raw, иначе в
        processed
    :return:
    """
    file_path = get_filepath(file_name, is_raw)
    if os.path.isfile(file_path):
        if os.path.getsize(file_path) > 0:
            return True
        os.remove(file_path)
    return False


def _delete_if_exist(file_path, is_raw):
    if is_data_exists(file_path, is_raw):
        os.remove(file_path)
    else:
        # создание директорий при необходимости
        base_dir = os.path.split(file_path)[0]
        os.makedirs(base_dir, exist_ok=True)


def open_file(file_name, is_raw):
    """ Открыть файл

    :param file_name: название файла с данными
    :param is_raw: сырые ли данные? если да - смотреть в папке raw, иначе в
        processed
    :return:
    """

    file_path = get_filepath(file_name, is_raw)

    # изменять время создания и модификации файла перед его открытием,
    # что позволяет найти неиспользуемые файлы по дате создания
    #timestamp = datetime.now().timestamp()
    #os.utime(file_path, (timestamp, timestamp))

    with open(file_path, mode='r', encoding='utf-8') as file:
        return file.read()


def write_data(file_name, data, is_raw):
    """ Записать данные в файл

    :param file_name: название файла с данными
    :param data: данные для записи
    :param is_raw: сырые ли данные? если да - смотреть в папке raw, иначе в
        processed
    :return:
    """
    file_path = get_filepath(file_name, is_raw)
    _delete_if_exist(file_path, is_raw)

    if type(data) == list or type(data) == dict:
        data = json.dumps(data, ensure_ascii=False)

    with open(file_path, mode='w', encoding='utf-8') as file:
        file.write(data)


def write_csv(file_name, header, data, is_raw):
    """ Записать данные в csv файл

    :param file_name: название файла с данными
    :param header: заголовок с названиями столбцов
    :param data: данные для записи (list)
    :param is_raw: сырые ли данные? если да - смотреть в папке raw, иначе в
        processed
    :return:
    """
    file_path = get_filepath(file_name, is_raw)
    _delete_if_exist(file_path, is_raw)

    with open(file_path, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(data)


def get_xgboost_path():
    return os.path.join(os.getcwd(), 'models', XGBOOST_MODEL)

