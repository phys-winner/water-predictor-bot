from src.secrets import water_level_login
from utils import AuthError, get_auth_data

import re
import requests

BASE = 'https://gmvo.skniivh.ru/'
LOGIN_URL = BASE + 'index.php?id=1'


def get_auth_cookies():
    """ Авторизация на сайте АИС ГМВО с получением cookie для дальнейшей работы
        с сайтом. Данные для авторизации находятся в src/secrets.py

        Благодаря анализу формы сайта и запросов после авторизации удалось
        определить логику работы логина:
        1. POST запросом вызывается https://gmvo.skniivh.ru/index.php?id=1
           с данными заполненной формы: логин/пароль, скрытые поля rememberme
           и cmdweblogin
        2. Если данные верны, то происходит редирект на index.php?id=505 с кодом
           302
        3. Если данные не верны, то заново запрашивается начальный сайт
           со статусом 200, однако в код страницы добавляется вызов alert
           с описанием ошибки:
           
           window.setTimeout("alert('Неверное имя пользователя или пароль!')"
    :return: словарь с cookie
    """
    form_data = get_auth_data()
    try:
        r = requests.post(LOGIN_URL, data=form_data, allow_redirects=False)
        if r.ok:
            if r.status_code == 302:
                # При успешной авторизации происходит редирект
                return r.cookies.get_dict()
            elif 'window.setTimeout("alert(\'' in r.text:
                error = re.search(r"window\.setTimeout\(\"alert\('(.+)'\)\"",
                                  r.text).group(1)
                print(error)
                raise AuthError(error)
            else:
                raise AuthError('Неизвестная ошибка при авторизации')
        else:
            raise r.raise_for_status()
    except Exception as e:
        raise e


print(get_auth_cookies())

