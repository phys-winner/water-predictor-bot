from xgboost import XGBRegressor
from sklearn.preprocessing import minmax_scale

import pandas as pd
import numpy as np

from utils import *
from gismeteo_parse import get_weather_data, is_gismeteo_cached


class Predictor:
    def __init__(self, posts):
        self.xgboost = XGBRegressor()
        self.xgboost.load_model(get_xgboost_path())
        self.posts = posts
        self.water_stats = pd.read_csv(get_filepath(DATA_WATER_STATS,
                                                    is_raw=False),
                                       dtype={'uid': str})

    def is_cached_data(self, uid, year, month):
        current_post = self.posts[uid]
        return is_gismeteo_cached(current_post, year, month)

    def predict(self, uid, year, month):
        current_post = self.posts[uid]

        weather_data = get_weather_data(current_post, year, month)
        df = _prepare_dataframe(uid, weather_data)
        predict = self.xgboost.predict(df.drop(['date'], axis=1))
        #predict = np.rint(predict)  # округление чисел до целых

        result = pd.DataFrame({
            "date": df['date'],
            "day_of_year": df['date'].dt.dayofyear,
            "result": predict
        })
        stats = self.water_stats[self.water_stats['uid'] == uid]
        stats = stats.drop(['uid'], axis=1)

        result = result.merge(stats, on='day_of_year', how='inner')
        return result


def _prepare_dataframe(uid, weather_data):
    # date, latitude, longitude, temperature, weather, is_fallback_data
    columns = ['date', 'latitude', 'longitude', 'temperature', 'weather',
               'is_fallback_data']
    df = pd.DataFrame(weather_data, columns=columns)
    df.insert(0, 'uid', uid)

    # добавляем строки с мин и макс значениями, после нормализации удалим их
    norm_info = open_file(DATA_NORMALIZATION, is_raw=True)
    norm_info = json.loads(norm_info)
    for row in norm_info:
        df.loc[len(df), df.columns] = row

    df['date'] = df['date'].astype('datetime64[ns]')
    #print(df.tail(3).T)

    # добавление строк с годом и синусом/косинусом дня в году
    total_years = np.where(df['date'].dt.is_leap_year, 366, 365)
    df['year'] = df['date'].dt.year
    df['day_sin'] = np.sin(
        2 * np.pi * df['date'].dt.dayofyear / total_years)
    df['day_cos'] = np.cos(
        2 * np.pi * df['date'].dt.dayofyear / total_years)

    # кодирование погоды
    df['weather_snow'] = df['weather'].map(
        {'clear': 0, 'rain': 0, 'storm': 0, 'snow': 1})
    df['weather_v3_rain'] = df['weather'].map(
        {'clear': 0, 'rain': 1, 'storm': 0, 'snow': 0})
    df['weather_v3_storm'] = df['weather'].map(
        {'clear': 0, 'rain': 0, 'storm': 1, 'snow': 0})

    df = df.drop(['weather'], axis=1)

    # нормализация
    columns_to_scale = ['uid', 'temperature', 'year', 'latitude',
                        'longitude']
    df[columns_to_scale] = minmax_scale(df[columns_to_scale])
    #print(df.tail(3).T)

    df = df[:-2]  # удаляем строки с данными для корректной нормализации
    #print(df.tail(3).T)
    return df

