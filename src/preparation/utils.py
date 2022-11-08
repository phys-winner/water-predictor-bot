from src.secrets import water_level_login


class AuthError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def get_auth_data():
    """ Возврат данных для авторизации на сайте АИС ГМВО.

    :return: словарь с данными
    """
    form_data = water_level_login
    form_data.update({
        'rememberme': 0,       # скрытый флаг Запомнить меня
        'cmdweblogin': 'Вход'
    })
    return form_data
