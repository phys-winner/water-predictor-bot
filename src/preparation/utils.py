from time import sleep

from src.secrets import water_level_login
import requests


class AuthError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def get_url(url, params=None, cookies=None):
    r = requests.get(url, params=params, cookies=cookies)
    r.raise_for_status()
    sleep(1)  # ждём, чтобы не перегрузить сайт запросами

    return r

def post_url(url, data=None, cookies=None, allow_redirects=True):
    r = requests.post(url, data=data, cookies=cookies)
    r.raise_for_status()
    sleep(1)  # ждём, чтобы не перегрузить сайт запросами

    return r

def get_auth_data():
    """ Возврат данных для авторизации на сайте АИС ГМВО.

    :return: словарь с данными
    """
    form_data = {
        'rememberme': 0,       # скрытый флаг Запомнить меня
        'cmdweblogin': 'Вход'
    }
    form_data.update(water_level_login)
    return form_data
