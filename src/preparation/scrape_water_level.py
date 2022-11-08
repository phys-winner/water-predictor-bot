from bs4 import BeautifulSoup
from src.preparation.utils import AuthError, get_auth_data, get_url, post_url
from src.utils import is_data_exists, open_json, write_data

import re
import json

BASE = 'https://gmvo.skniivh.ru/'
LOGIN_URL = BASE + 'index.php?id=1'

API_POSTFIX = BASE + 'eais/forms/'
GET_DISTRICTS_URL = API_POSTFIX + 'get_bo.php'
GET_POOLS_URL = API_POSTFIX + 'get_rb.php'
GET_SUBPOOLS_URL = API_POSTFIX + 'get_sb.php'
GET_POSTS_URL = API_POSTFIX + 'get_hpr.php'


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
    r = post_url(LOGIN_URL, data=form_data, allow_redirects=False)
    if r.status_code == 302:
        # При успешной авторизации происходит редирект
        return r.cookies.get_dict()
    elif 'window.setTimeout("alert(\'' in r.text:
        error = re.search(r"window\.setTimeout\(\"alert\('(.+)'\)\"",
                          r.text).group(1)
        raise AuthError(f'Ошибка при авторизации: {error}')
    else:
        raise AuthError('Неизвестная ошибка при авторизации')


def get_posts_uids(auth_cookie, district, pool, subpools):
    """ Получение данных ежедневных наблюдений через формы страницы
        https://gmvo.skniivh.ru/index.php?id=180

        Обращение
    :param auth_cookie: куки с авторизацией из функции get_auth_cookies()
    :param district: бассейновый округ
    :param pool: бассейн
    :param subpools: подбассейны (list)
    :return:
    """

    def get_data(url, req_params, target_string, field='uid', target_name=None):
        def get_data_from_list(work_list, target):
            result = next(x[field]
                          for x in work_list
                          if target in x['NAME'])
            if result == -1:
                raise Exception(f"{target_name} {target} не найден")
            return result

        prefix = re.search(r"/(\w+)\.php", url).group(1)
        file_name = f'water_{prefix}_{target_name}_{target_string}.json'
        if is_data_exists(file_name, is_raw=True):
            lst = open_json(file_name, is_raw=True)
        else:
            r = get_url(url, params=req_params, cookies=auth_cookie)
            soup = BeautifulSoup(r.text, 'lxml')
            lst = json.loads(soup.text)

            write_data(file_name, data=json.dumps(lst, ensure_ascii=False),
                       is_raw=True)

        if type(target_string) == list:
            # возврат всех uid при пустом списке используется для постов
            if len(target_string) == 0:
                return [x[field] for x in lst]

            # получение нескольких uid по списку, используется для подбассейнов
            return [int(get_data_from_list(lst, target))
                    for target in target_string]
        else:
            return get_data_from_list(lst, target_string)

    posts_file_name = 'water_posts_uids.json'
    if is_data_exists(posts_file_name, is_raw=True):
        return open_json(posts_file_name, is_raw=True)

    # Получение ид бассейного округа по его названию
    params = {'sea': 0}
    district_uid = get_data(GET_DISTRICTS_URL, params,
                            target_string=district,
                            target_name='Бассейновый округ')
    # district_uid = 17

    # Получение ид бассейна по его названию через ид бассейнового округа
    params = {'uid': district_uid}
    pool_uid = get_data(GET_POOLS_URL, params,
                        target_string=pool,
                        target_name='Бассейн')
    # pool_uid = 17

    # Получение списка подбассейнов по их названиям через ид бассейна
    params = {'uid': pool_uid}
    subpool_uids = get_data(GET_SUBPOOLS_URL, params,
                            target_string=subpools,
                            target_name='Подбассейны')
    # subpool_uids = [114, 124]

    posts = []
    for subpool_uid in subpool_uids:
        params = {
            'table': 'gm_waterlevel_river,'
                     'gm_waterlevel_river_day,'
                     'gm_waterlevel_river_month,'
                     'gm_waterlevel_river_decade',
            'sbo': district_uid,
            'srb': pool_uid,
            'ssb': subpool_uid,
            'shep': 0,
            'uid_form': 7
        }
        posts.extend(get_data(GET_POSTS_URL, params,
                              field='kod_hp', target_string=list()))

    posts = list(set(posts))  # преобразование к set очищает list от дубликатов
    write_data(posts_file_name, data=json.dumps(posts, ensure_ascii=False),
               is_raw=True)
    return posts


def main():
    auth_cookie = get_auth_cookies()

    # параметры, по которым необходимо получить наблюдения
    start_year = 2008
    end_year = 2017

    years = [x for x in range(start_year, end_year + 1)]
    district = 'Енисейский бассейновый округ'
    pool = 'Енисей (российская часть бассейна)'
    subpools = ['Подкаменная Тунгуска', 'Нижняя Тунгуска']

    posts_uids = get_posts_uids(auth_cookie, district, pool, subpools)


if __name__ == '__main__':
    main()
