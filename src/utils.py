import json
import os.path
import re
import os


DATA_WATER_RAW = 'water_data.html'

def _get_filepath(file_name, is_raw):
    file_name = re.sub(r'[^\wА-Яа-яёЁ_.)( -]', '', file_name)  # чистка имени
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
    file_path = _get_filepath(file_name, is_raw)
    return os.path.isfile(file_path)


def open_json(file_name, is_raw):
    """ Открыть json файл

    :param file_name: название файла с данными
    :param is_raw: сырые ли данные? если да - смотреть в папке raw, иначе в
        processed
    :return:
    """
    file_path = _get_filepath(file_name, is_raw)
    with open(file_path, mode='r', encoding='utf-8') as file:
        return json.loads(file.read())


def write_data(file_name, data, is_raw):
    """ Записать данные в файл

    :param file_name: название файла с данными
    :param data: данные для записи
    :param is_raw: сырые ли данные? если да - смотреть в папке raw, иначе в
        processed
    :return:
    """
    file_path = _get_filepath(file_name, is_raw)
    if is_data_exists(file_path, is_raw):
        os.remove(file_path)

    if type(data) == list or type(data) == dict:
        data = json.dumps(data, ensure_ascii=False)

    with open(file_path, mode='w', encoding='utf-8') as file:
        file.write(data)
