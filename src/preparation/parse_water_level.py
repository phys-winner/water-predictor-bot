from calendar import monthrange

from bs4 import BeautifulSoup
from htmlmin import minify

from src.preparation.utils import AuthError, get_auth_data
from src.utils import *

BASE = 'https://gmvo.skniivh.ru/'
LOGIN_URL = BASE + 'index.php?id=1'
GET_DATA_URL = BASE + 'index.php?id=544&sname=form14_output&spar=%26variant%3D0'

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


def get_data_posts(auth_cookie, district, pool, subpools):
    """ Получение uid постов с формы https://gmvo.skniivh.ru/index.php?id=180

        Алгоритм работы:
        1. Во время загрузки формы для получения списка бассейновых округов
           происходит GET запрос к
           https://gmvo.skniivh.ru/eais/forms/get_bo.php

           Функция получает этот список для поиска uid заданного округа

        2. После этого для получения списка бассейнов, принадлежащих текущему
           округу, делается GET запрос с параметром uid округа

           https://gmvo.skniivh.ru/eais/forms/get_rb.php?uid=

           Функция получает этот список для поиска uid заданного бассейна

        3. Также происходит с получением списка подбассейнов по uid бассейна:
           https://gmvo.skniivh.ru/eais/forms/get_sb.php?uid=

        4. Нажатие на кнопку "Найти" для получения списка всех постов делает GET
           запрос с множеством параметров (см. ниже, GET_POSTS_URL) к
           https://gmvo.skniivh.ru/eais/forms/get_hpr.php

        Результаты всех запросов сохраняются в data\raw\
    :param auth_cookie: куки с авторизацией из функции get_auth_cookies()
    :param district: бассейновый округ
    :param pool: бассейн
    :param subpools: подбассейны (list)
    :return: список uid постов наблюдения
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
            file = open_file(file_name, is_raw=True)
            lst = json.loads(file)
        else:
            r = get_url(url, params=req_params, cookies=auth_cookie)
            # Открытие текста запроса в bs4 для последующего корректного
            # перевода в json вместе с декодированием юникод последовательностей
            soup = BeautifulSoup(r.text, 'lxml')
            lst = json.loads(soup.text)

            write_data(file_name, data=lst, is_raw=True)

        if type(target_string) == list:
            # получение нескольких uid по списку, используется для подбассейнов
            return [int(get_data_from_list(lst, target))
                    for target in target_string]
        else:
            return get_data_from_list(lst, target_string)

    if is_data_exists(DATA_POSTS_RAW, is_raw=True):
        file = open_file(DATA_POSTS_RAW, is_raw=True)
        return json.loads(file)

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

    posts = {}  # uid: name
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
        file_name = f'water_get_hpr_{subpool_uid}.json'
        if is_data_exists(file_name, is_raw=True):
            subpool_info = open_file(file_name, is_raw=True)
            lst = json.loads(subpool_info)
        else:
            r = get_url(GET_POSTS_URL, params=params, cookies=auth_cookie)
            soup = BeautifulSoup(r.text, 'lxml')
            subpool_info = soup.text

            lst = json.loads(subpool_info)
            write_data(file_name, data=lst, is_raw=True)

        posts.update({entry['kod_hp']: {'name': entry['name_hp'],
                                        'subpool_id': entry['attachment'],
                                        'cadid': entry['CADID'],
                                        'water_site': entry['name_wo']}
                      for entry in lst})

    write_data(DATA_POSTS_RAW, data=posts, is_raw=True)
    return posts


def get_water_data(auth_cookie, years, posts_data):
    """ Получение данных ежедневных наблюдений по постам наблюдений.

    :param auth_cookie: куки с авторизацией из функции get_auth_cookies()
    :param years: список годов, за которые нужно получить данные
    :param posts_data: список постов наблюдений, словарь uid: название
    :return:
    """
    form_data = {
        'submit': 1,
        'pid': 180,
        'table': 'gm_waterlevel_river,'
                 'gm_waterlevel_river_day,'
                 'gm_waterlevel_river_month,'
                 'gm_waterlevel_river_decade',
        'data_year[]': years,
        'uid_form': 7,
        'data_kod_hpr[]': posts_data.keys()
    }
    r = post_url(GET_DATA_URL, data=form_data, cookies=auth_cookie)
    write_data(DATA_WATER_RAW, data=minify(r.text), is_raw=True)


def form_dataset():
    """ Формирование датасета: id_поста,дата,уровень_воды
    """
    water_data = open_file(DATA_WATER_RAW, is_raw=True)
    soup = BeautifulSoup(water_data, 'lxml')

    # Данные с информацией о постах находятся в таблицах с классом table
    info_tables = soup.findAll('table', {'class': ['table']})

    # В таблицах с классом calend помимо необходимых наблюдений есть данные
    # о статистике за год (низший, средний и высший уровни за год)
    # они не нужны, т.к. при необходимости их можно вычислить средствами pandas
    data_tables = soup.findAll('table', {'class': ['calend']})[::2]

    if len(info_tables) != len(data_tables):
        raise Exception('Число таблиц с информацией не совпадает '
                        'с числом таблиц с наблюдениями.')

    result_data = []  # id_поста,дата,уровень_воды
    result_info = {}  # id_поста,отметка_нуля,система_высот
    id_list = ['kod_hpr', 'year', 'altitude', 'alt_system']
    for i in range(len(info_tables)):
        # информация
        info_table = info_tables[i]
        infos = [info.text for info in info_table.find_all('p', id=id_list)]
        uid = infos[0]
        year = int(infos[1])
        [altitude, alt_system] = infos[2:]

        if uid in result_info and result_info[uid] != [altitude, alt_system]:
            raise Exception(f'У поста {uid} изменена отметка нуля '
                            f'или система высот')
        result_info[uid] = [altitude, alt_system]

        # наблюдение
        data_table = data_tables[i]
        data_rows = data_table.find_all('tr')[1:]  # убираем заголовок
        data_rows = data_rows[:31]  # убираем статистическую информацию
        if data_rows[0].find('td').text != '1':
            raise Exception('В таблице не обнаружено первое число.')
        for row in data_rows:
            cells = row.find_all('td')
            day = int(cells[0].text)
            for month in range(0, 12):
                # не во всех месяцах есть данные за все 31 день, пропускаем их
                if day > monthrange(year, month + 1)[1]:
                    continue
                water_level = cells[month + 1].text.strip()
                if len(water_level) == 0 or \
                        '-' in water_level or \
                        water_level == 'прмз' or \
                        water_level == 'прсх' or \
                        water_level == 'пр' or \
                        water_level == 'прс' or \
                        water_level == 'прм':
                    # пусто или тире - данные не велись, пример - Кербо 2008
                    # прмз - река промерзла или пересохла
                    # прмз - река промерзла или пересохла
                    # расшифровка остальных не указана
                    continue
                else:
                    try:
                        water_level = re.search(r'\d+', water_level).group(0)
                    except Exception as e:
                        print(row)
                        print(water_level)
                        raise e
                result_data.append([uid,
                                    format_data(year, month + 1, day),
                                    water_level])
                # for day in range(0, monthrange(year, month + 1)[1]):
                # print(month + 1, day + 1)
        '''
        for month in range(0, 12):
            row = data_rows[month]
            print(row)
            #for day in range(0, monthrange(year, month + 1)[1]):
                #print(month + 1, day + 1)
                '''

    header = ['uid', 'date', 'water_level']
    result_data = sorted(result_data)
    write_csv(DATA_WATER_LEVEL, header, result_data, is_raw=True)
    # print(result_data)


def main():
    """ Запуск процесса парсинга данных наблюдений с постов с сайта АИС ГМВО
    с последующим формированием датасета.
    Порядок действий:
    1. Авторизация;
    2. Получение списка с идентификаторами постов наблюдения;
    3. Получение необходимых данных с сохранением в data\raw\water_data.html;
    4. Формирование датасета.
    """
    if is_data_exists(DATA_WATER_LEVEL, is_raw=True):
        print('Датасет со всеми данными наблюдений уже сформирован')
        return
    if is_data_exists(DATA_WATER_RAW, is_raw=True):
        print('Данные ежедневных наблюдений по постам уже были получены')
    else:
        auth_cookie = get_auth_cookies()
        print('Signed in')

        # параметры, по которым необходимо получить наблюдения
        years = [x for x in range(START_YEAR, END_YEAR + 1)]
        district = 'Енисейский бассейновый округ'
        pool = 'Енисей (российская часть бассейна)'
        subpools = ['Подкаменная Тунгуска', 'Нижняя Тунгуска']

        posts_data = get_data_posts(auth_cookie, district, pool, subpools)
        print('Obtained posts data')
        get_water_data(auth_cookie, years, posts_data)
        print('Got info about water level')
    form_dataset()


if __name__ == '__main__':
    main()
