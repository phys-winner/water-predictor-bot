from secret_auth import water_level_login


class AuthError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def get_auth_data():
    """ Возврат данных для авторизации на сайте АИС ГМВО.

    :return: словарь с данными
    """
    form_data = {
        'rememberme': 0,  # скрытый флаг Запомнить меня
        'cmdweblogin': 'Вход'
    }
    form_data.update(water_level_login)
    return form_data
