from bs4 import BeautifulSoup
from htmlmin import minify
from calendar import monthrange

from src.preparation.utils import AuthError, get_auth_data
from src.utils import *

# В данный модуль выделен код для обработки страниц Gismeteo из ноутбука
# notebooks\parse_gismeteo.ipynb


def get_cached_filename(gismeteo_id, year, month):
    return os.path.join('gismeteo', str(gismeteo_id), f'{year}-{month:02d}.html')

def get_gismeteo_table(gismeteo_id, year, month):
    file_name = get_cached_filename(gismeteo_id, year, month)
    if is_data_exists(file_name, is_raw=True):
        weather = open_file(file_name, is_raw=True)
        soup = BeautifulSoup(weather, 'lxml')
        if soup.find(class_='empty_phrase'):
            return None
        return soup
    else:
        url = f'https://www.gismeteo.ru/diary/{gismeteo_id}/{year}/{month}/'
        r = get_url(url)
        weather = r.text
        soup = BeautifulSoup(weather, 'lxml')
        empty_phrase = soup.find(class_='empty_phrase')
        if empty_phrase:
            write_data(file_name, data=str(empty_phrase), is_raw=True)
            return None

        table = soup.find('table')
        # для формирования форматированных html-страниц (с отступами и
        # переносами строк) можно использовать table.prettify(), для минификации
        # (максимально возможного сокращения размера html без потери
        # функционала) - сторонний модуль htmlmin
        write_data(file_name, data=minify(str(table)), is_raw=True)
        return table

def process_history_row(row):
    cells = row.find_all('td')

    # day, temperature
    def get_cell_int(cell_id):
        if cell_id > 10:
            return None
        val = cells[cell_id].text
        if val == '−' or len(val) == 0:
            # если за день нет информации, то берём её за вечер
            return get_cell_int(cell_id + 5)

        return int(val)

    day = get_cell_int(0)
    temperature = get_cell_int(1)

    # weather
    def get_cell_img(cell_id):
        if cell_id > 10:
            return None
        imgs = cells[cell_id].find_all('img')
        if len(imgs) > 0:
            if len(imgs) > 2:
                # обычно в ячейке находятся 2 картинки - цветная и ч/б
                raise Exception(f"больше, чем 2 картинки")
            img = imgs[0]['src']  # //st6.gismeteo.ru/static/diary/img/dull.png
            if img.endswith('still.gif'):
                return get_cell_img(cell_id + 5)
            return re.search(r"diary/img/(\w+).png", img).group(1)
        return 'clear'

    weather = get_cell_img(4)

    # в реальных долгосрочных прогнозах погоды на весь день даётся 1 прогноз, который содержит
    # минимальную и максимальную температуру, облачность и наличие осадков.

    return [day, temperature, weather]


def form_historical_dataset(post, year, month):
    result = []
    print(f"{post['name']} - год {year}")
    def get_data_rows(gismeteo_id):
        table = get_gismeteo_table(gismeteo_id, year, month)
        if not table:
            return None

        data_rows = table.find_all('tr')
        return data_rows[2:]  # убрать шапку таблицы

    # В приоритете используются метео-данными из основного источника, если их
    # Примеры неполных метеоданных:
    # с 18 + пропуски https://www.gismeteo.ru/diary/158155/2015/3/
    # до 19 числа https://www.gismeteo.ru/diary/4015/2015/9/
    # с 29 по 31 https://www.gismeteo.ru/diary/4015/2015/10/
    main_data = get_data_rows(post['gismeteo_id'])
    main_gps = [post['latitude'], post['longitude']]
    fallback_dict = None
    fallback_gps = None

    if not main_data or (
            len(main_data) < monthrange(year, month)[1]
            and 'fallback' in post.keys()):
        fallback_gps = [post['fallback']['latitude'],
                        post['fallback']['longitude']]
        fallback_data = get_data_rows(
            post['fallback']['gismeteo_id'])
        if not fallback_data:
            # в течении месяца нет информации ни у оригинального источника,
            # ни у дополнительного
            return None
        if main_data:
            fallback_data = [process_history_row(row) for row in
                             fallback_data]
            fallback_dict = {
                day: (temperature, weather, 1)  # 1 is is_fallback_data
                for day, temperature, weather in fallback_data}
        else:
            main_data = fallback_data
            main_gps = fallback_gps

    is_fallback = int(main_gps == fallback_gps or post[
        'clean_name'] == 'Светлана')  # check if it is Светлана
    day = 1
    for row in main_data:
        try:
            data = process_history_row(row)
        except Exception:
            err_str = f"check https://www.gismeteo.ru/diary/{post['gismeteo_id']}/{year}/{month}/"
            if 'fallback' in post.keys():
                err_str += f"\n+ https://www.gismeteo.ru/diary/{post['fallback']['gismeteo_id']}/{year}/{month}/"
            raise Exception(err_str)

        row_day = data[0]
        while day != row_day:
            # если есть пропуски в днях в основном источнике метео-данных
            if fallback_dict:
                # то заполняем пропуски из второстепенного источника
                if day in fallback_dict:
                    date_string = f'{year}-{month:02d}-{day:02d}'
                    result.append([date_string] + fallback_gps + list(
                        fallback_dict[day]))
                    day += 1
                    continue

            # в обоих источниках есть пропуски данных - игнорируем
            day += 1

        date_string = f'{year}-{month:02d}-{row_day:02d}'
        result.append([date_string] + main_gps + data[1:] + [is_fallback])
        day += 1
    return result


def is_gismeteo_cached(post, year, month):
    file_name = get_cached_filename(post['gismeteo_id'], year, month)
    return is_data_exists(file_name, is_raw=True)


def get_weather_data(post, year, month):
    return form_historical_dataset(post, year, month)

