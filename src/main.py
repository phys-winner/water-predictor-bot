import calendar
import locale
import logging

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

uids_list = list(posts_info.keys())
year_list = [x for x in range(2018, datetime.now().year + 1)]

predictor = Predictor(posts_info)

def invalid_data_msg(update: Update):
    update.callback_query.message.reply_text(INVALID_DATA_MESSAGE,
                                         reply_markup=ReplyKeyboardRemove())
    return False


def check_callback_date(update: Update):
    """ Проверка значений, переданных через Callback кнопок.
    Обычный пользователь всегда будет проходить данные проверки.
    """
    callback_data = update.callback_query.data
    print(callback_data)
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
                and month > datetime.now().month) \
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
    for uid, post in posts_info.items():
        keyboard.append([InlineKeyboardButton(text=post['name'],
                                              callback_data=uid)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(START_MESSAGE)
    update.message.reply_text(SELECT_POST, reply_markup=reply_markup)
    return YEAR


def select_year(update: Update, context: CallbackContext):
    uid, _, _ = check_callback_date(update)
    if not uid:
        return ConversationHandler.END

    reply_keyboard = []
    for i, year in enumerate(year_list):
        reply_keyboard.append(InlineKeyboardButton(text=str(year),
                                                   callback_data=f'{uid}-'
                                                                 f'{year}'))
    reply_markup = InlineKeyboardMarkup([reply_keyboard])

    # update.callback_query.edit_message_reply_markup(None)  # скрыть клавиатуру
    update.callback_query.message.edit_text(SELECT_YEAR,
                                            reply_markup=reply_markup)
    return MONTH


def select_month(update: Update, context: CallbackContext):
    uid, year, _ = check_callback_date(update)
    if not uid:
        return ConversationHandler.END

    reply_keyboard = []
    last_month = 12
    if year == datetime.now().year:
        last_month = datetime.now().month - 1 + 1

    reply_row = []
    for month in range(1, last_month + 1):
        month_str = f'{month} {calendar.month_name[month].lower()}'

        reply_row.append(InlineKeyboardButton(text=str(month_str),
                                              callback_data=f'{uid}-{year}-{month}'))
        if month % 4 == 0:
            reply_keyboard.append(reply_row)
            reply_row = []

    if len(reply_row) > 0:
        reply_keyboard.append(reply_row)

    reply_markup = InlineKeyboardMarkup(reply_keyboard)
    update.callback_query.message.edit_text(SELECT_MONTH,
                                            reply_markup=reply_markup)
    return PREDICT


def predict(update: Update, context: CallbackContext):
    uid, year, month = check_callback_date(update)
    if not uid:
        return ConversationHandler.END
    result = predictor.predict(uid, year, month)
    print(result)
    update.callback_query.message.edit_text(str(result), reply_markup=None)
    #update.callback_query.message.edit_text(PREDICT_MESSAGE.format(uid, year, month),
    #                                        reply_markup=None)
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Вы успешно отменили запрос.',
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main():
    """ Запуск бота Telegram.
    Алгоритм работы:
    1. /start - запрос у пользователя выбора поста наблюдения из списка (inline)
    2. Выбор года предсказания
    3. Выбор месяца
    4. Вывод прогноза
    """
    # Запуск бота
    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher

    uid_regexp = r'^(\d+)$'
    year_regexp = r'^(\d+-\d{4})$'
    month_regexp = r'^(\d+-\d{4}-\d+)$'

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            YEAR: [CallbackQueryHandler(select_year, pattern=uid_regexp)],
            MONTH: [CallbackQueryHandler(select_month, pattern=year_regexp)],
            PREDICT: [CallbackQueryHandler(predict, pattern=month_regexp)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],

    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
