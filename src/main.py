import calendar
import locale
import logging
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
from io import BytesIO

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import CallbackContext, ConversationHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext import Updater, CommandHandler

from src.secret_auth import tg_bot_token
from src.strings_ru import *
from src.utils import *
from src.predict import Predictor

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)
locale.setlocale(locale.LC_ALL, 'ru_RU')

YEAR, MONTH, PREDICT = range(3)
posts_info = open_file(DATA_POSTS_FULL_RAW, is_raw=True)
posts_info = json.loads(posts_info)
posts_info = {k: v for k, v in
              sorted(posts_info.items(), key=lambda x: x[1]['name'])}
sub_pools = {post['subpool_id']: post['subpool_name']
             for post in posts_info.values()}

uids_list = list(posts_info.keys())
year_list = [x for x in range(2018, datetime.now().year + 1)]

predictor = Predictor(posts_info)


def invalid_data_msg(update: Update):
    update.callback_query.message.reply_text(INVALID_DATA_MESSAGE,
                                             reply_markup=ReplyKeyboardRemove())
    return False


def get_month_name(month, pretty=False):
    result = calendar.month_name[month]
    if pretty:
        emoji = '🌱'  # весна
        if month == 12 or month <= 2:  # зима
            emoji = '❄'
        elif month >= 9:  # осень
            emoji = '🍂'
        elif month >= 6:  # лето
            emoji = '☀'
        result = f'{emoji} {result}'
    return result

def check_callback_date(update: Update):
    """ Проверка значений, переданных через Callback кнопок.
    Обычный пользователь всегда будет проходить данные проверки.
    """
    callback_data = update.callback_query.data
    callback_data = callback_data.split("-")
    uid, year, month = None, None, None
    is_valid = True

    if len(callback_data) >= 2:  # uid поста-год
        try:
            year = int(callback_data[1])
            if year not in year_list:
                is_valid &= invalid_data_msg(update)
        except:
            is_valid &= invalid_data_msg(update)

    if is_valid and len(callback_data) >= 3:  # uid поста-год-месяц
        try:
            month = int(callback_data[2])

            if (year == datetime.now().year
                and month > datetime.now().month + 1) \
                    or month > 12 \
                    or month < 1:
                is_valid &= invalid_data_msg(update)
        except:
            is_valid &= invalid_data_msg(update)

    if is_valid and len(callback_data) >= 1:  # uid поста
        try:
            uid = callback_data[0]
            if uid not in uids_list:
                is_valid &= invalid_data_msg(update)
        except:
            is_valid &= invalid_data_msg(update)

    if not is_valid:
        return None, None, None

    return uid, year, month


def start(update: Update, context: CallbackContext):
    keyboard = []
    for uid, name in sub_pools.items():
        keyboard.append([InlineKeyboardButton(text=name,
                                              callback_data=f'query-' + uid)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        update.callback_query.message.edit_text(SELECT_SUBPOOL,
                                                parse_mode='HTML',
                                                reply_markup=reply_markup)
    else:
        update.message.reply_text(START_MESSAGE + SELECT_SUBPOOL,
                                  parse_mode='HTML',
                                  reply_markup=reply_markup)


def select_post(update: Update, context: CallbackContext):
    callback_data = update.callback_query.data
    callback_data = callback_data.split("-")
    if len(callback_data) < 2 or callback_data[1] not in sub_pools.keys():
        return invalid_data_msg(update)

    subpool_uid = callback_data[1]
    formatted_msg = SELECT_POST.format(sub_pools[subpool_uid])
    keyboard = []
    for uid, post in posts_info.items():
        if subpool_uid == post['subpool_id']:
            keyboard.append([InlineKeyboardButton(text=post['name'],
                                                  callback_data=uid)])

    #keyboard = [keyboard]
    keyboard.append([InlineKeyboardButton(
        text=BACK_LABEL,
        callback_data='start')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.edit_text(formatted_msg,
                                            parse_mode='HTML',
                                            reply_markup=reply_markup)

def select_year(update: Update, context: CallbackContext):
    uid, _, _ = check_callback_date(update)
    if not uid:
        return

    formatted_msg = SELECT_YEAR.format(posts_info[uid]['name'])
    keyboard = []
    for i, year in enumerate(year_list):
        keyboard.append(InlineKeyboardButton(text=str(year),
                                                   callback_data=f'{uid}-'
                                                                 f'{year}'))
    keyboard = [keyboard]
    keyboard.append([InlineKeyboardButton(
        text=BACK_LABEL,
        callback_data='query-' + posts_info[uid]['subpool_id'])])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.edit_text(formatted_msg,
                                            parse_mode='HTML',
                                            reply_markup=reply_markup)


def select_month(update: Update, context: CallbackContext):
    uid, year, _ = check_callback_date(update)
    if not uid:
        return

    formatted_msg = SELECT_MONTH.format(posts_info[uid]['name'], year)
    keyboard = []
    last_month = 12
    if year == datetime.now().year:
        last_month = datetime.now().month - 1

    reply_row = []
    for month in range(1, last_month + 1):
        month_str = get_month_name(month, pretty=True).lower()

        reply_row.append(InlineKeyboardButton(text=str(month_str),
                                              callback_data=f'{uid}-{year}-'
                                                            f'{month}'))
        if month % 4 == 0:
            keyboard.append(reply_row)
            reply_row = []

    if len(reply_row) > 0:
        keyboard.append(reply_row)

    keyboard.append([InlineKeyboardButton(text=BACK_LABEL,
                                                callback_data=f'{uid}')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.edit_text(formatted_msg,
                                            parse_mode='HTML',
                                            reply_markup=reply_markup)


def predict(update: Update, context: CallbackContext):
    uid, year, month = check_callback_date(update)
    if not uid:
        return
    if not predictor.is_cached_data(uid, year, month):
        update.callback_query.message.edit_text(PLEASE_WAIT_MESSAGE,
                                                reply_markup=None)
    result = predictor.predict(uid, year, month)

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.lineplot(data=result, y='result', x='date', label=PREDICTED_VALUE,
                 ax=ax, linewidth=5)
    sns.lineplot(data=result, y='min', x='date', label=HISTORY_MIN,
                 linestyle='dashed', ax=ax, linewidth=3)
    sns.lineplot(data=result, y='mean', x='date', label=HISTORY_MEAN,
                 linestyle='dotted', ax=ax, linewidth=3)
    sns.lineplot(data=result, y='max', x='date', label=HISTORY_MAX,
                 linestyle='dashed', ax=ax, linewidth=3)

    # после заполнения цветом график сдвигается вверх, необходимо сохранить
    # ограничение графика по y и его же установить после заполнения
    orig_ylim = ax.get_ylim()
    ax.fill_between(result['date'], result['result'], alpha=0.2)
    ax.set_ylim(orig_ylim)

    plt.grid()
    plt.legend()
    plt.xticks(result['date'], labels=[x + 1 for x in range(result.shape[0])])
    plt.xlabel(get_month_name(month))
    plt.ylabel(WATER_LEVEL)
    plt.suptitle(posts_info[uid]['name'])
    plt.title(PREDICT_TITLE.format(get_month_name(month).lower(), year))

    # уменьшение боковых отступов
    xlim = ax.get_xlim()
    xmargin = (xlim[1] - xlim[0]) * -0.045
    ax.set_xlim(xlim[0] - xmargin, xlim[1] + xmargin)

    post = posts_info[uid]
    yandex_url = f"https://yandex.ru/maps/?ll={post['longitude']}%2C{post['latitude']}&z=14"
    formatted_msg = PREDICT_MESSAGE.format(post['name'],
                                           get_month_name(month).lower(), year,
                                           post['subpool_name'],
                                           yandex_url,
                                           f"https://ru.wikipedia.org/wiki/{post['wiki_page']}",
                                           f"https://www.gismeteo.ru/diary/{post['gismeteo_id']}/{year}/{month}")

    with BytesIO() as img:
        plt.savefig(img, format='png')
        plt.close()

        img.seek(0)
        context.bot.send_photo(chat_id=update.callback_query.message.chat_id,
                               photo=img, parse_mode='HTML',
                               caption=formatted_msg)

    update.callback_query.message.delete()


def main():
    """ Запуск бота Telegram.
    Алгоритм работы:
    1. /start - запрос у пользователя выбора поста наблюдения из списка (inline)
    2. Выбор года предсказания
    3. Выбор месяца
    4. Вывод прогноза
    """
    matplotlib.use('Agg')  # отключить интерактивный режим matplotlib

    # Запуск бота
    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher

    uid_regexp = r'^(\d+)$'
    year_regexp = r'^(\d+-\d{4})$'
    month_regexp = r'^(\d+-\d{4}-\d+)$'
    subpool_regexp = r'^query-\d+$'
    start_regexp = r'^start$'

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(start,
                                                pattern=start_regexp))
    dispatcher.add_handler(CallbackQueryHandler(select_post,
                                                pattern=subpool_regexp))
    dispatcher.add_handler(CallbackQueryHandler(select_year,
                                                pattern=uid_regexp))
    dispatcher.add_handler(CallbackQueryHandler(select_month,
                                                pattern=year_regexp))
    dispatcher.add_handler(CallbackQueryHandler(predict,
                                                pattern=month_regexp))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
