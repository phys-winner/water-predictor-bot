![App Icon](images/description_picture.png)
# Water Predictor

**Water Predictor** - это написанный на Python бот в Telegram (протестировать: [@water_predictor_example_bot](https://t.me/water_predictor_example_bot)), который предсказывает уровень воды на постах гидрологического контроля рек **Подкаменная Тунгуска** и **Нижняя Тунгуска**, используя исторические метео-данные сервиса [Gismeteo.Дневник](https://www.gismeteo.ru/diary/) и машинное обучение.

![Пример поста с прогнозом](images/example_post.png)

Данное приложение является итоговым проектом для курса **Аналитик данных (Data scientist)** МГТУ им. Н.Э. Баумана от слушателя Плужника Евгения Николаевича.

<details><summary><b>Описание задания</b></summary>


По территории Красноярского края протекает огромное количество рек, многие из этих рек являются судоходными и являются важнейшими транспортными путями. Однако навигация в Енисейском бассейне крайне сложна. Многие реки являются судоходными лишь в короткий период половодья. Точно предсказать срок навигации на таких реках – важнейшая задача.

Ежегодно в Красноярском крае происходит «северный завоз» – комплекс мероприятий по доставке речным транспортом необходимых запасов, оборудования и материалов в населенные пункты, до которых можно добраться только по рекам. К таким поселениям относятся, например, поселок городского типа Тура на реке Нижняя Тунгуска или поселок Ванавара на реке Подкаменная Тунгуска. Помимо обеспечения населения, также доставляются грузы в места разработки полезных ископаемых, например, на Ванкорское нефтяное месторождение в бассейне реки Большая Хета.

Каждый год время начала и окончания навигации смещается в зависимости от фактических метеоусловий (температура и осадки в период таянья снега), запасов снега в бассейне рек. В ожидании достаточного уровня воды в устьях рек собираются караваны судов. Судам необходимо не только подняться вверх по течению до пункта назначения, но и вернуться обратно до того, как уровень воды упадет до критической отметки. Нередки случаи, когда суда оказывались на мели до следующего сезона «большой воды» или получали повреждения из-за низкого уровня воды. При этом уровень воды на некоторых реках может меняться на десятки метров всего за несколько дней.

Навигация затрудняется не только меняющимся уровнем воды, но и сложным рельефом русел. Так, например, на реке Нижняя Тунгуска при подъеме воды в Большом пороге выше отметки 30 метров, порог считается непреодолимым. И суда стоят в ожидании падения уровня воды, а затем буксируются вверх по порогу по очереди. Это сильно сказывается на сроках пути.

Для прогнозирования уровня рек предлагается использовать собранные за 2008-2017 года ежедневные наблюдения по постам гидрологического контроля рек Подкаменная Тунгуска (12 гидрологических постов) и Нижняя Тунгуска (15 гидрологических постов). В файлах с данными представлена информация и легенда с каждого из гидрологических постов. Информация за каждый год находится в отдельном файле. Также можно получать фактические данные с [https://gmvo.skniivh.ru/](https://gmvo.skniivh.ru/) после регистрации.

Требуется:
1) проверить гипотезу о достаточности данных об уровнях рек с постов гидрологического контроля, а также данных метеосводок для решения задачи прогнозирования периода навигации на сезон;
2) в случае положительного результата по п. 1, провести прогнозирование периода навигации на сезон.

В рамках выполнения итогового проекта необходимо для одного из предложенных кейсов (либо для кейса, предложенного обучающимся) выполнить следующие этапы:

1.  Предварительная обработка датасета.
    
2.  Применение минимум 3-х алгоритмов машинного обучения (включая обязательно использование искусственных нейронных сетей) в Jupyter Notebook (или colab) позволяющих решить поставленную задачу анализа данных, выбрать лучшую модель и применить ее в приложении.
    
3.  Создание локального репозитория git.
    
4.  Реализация приложения. Приложение может быть консольное, оконное или веб-приложение по выбору.
    
5.  Создание профиля на github.com
    
6.  Выгрузка коммитов приложения из локального репозитория на github.com.

</details>

# Этапы разработки приложения

В рамках выполнения проекта:
1. [*src/preparation/parse_water_level.py*](src/preparation/parse_water_level.py)

Разработан парсер данных наблюдений с постов гидрологического контроля сайта **АИС ГМВО** (автоматизированной информационной системы государственного мониторинга водных объектов Российской Федерации).

2. [*notebooks/parse_gismeteo.ipynb*](notebooks/parse_gismeteo.ipynb)

Разработан парсер исторических метео-данных сервиса [Gismeteo.Дневник](https://www.gismeteo.ru/diary/).

3. [*notebooks/eda.ipynb*](notebooks/eda.ipynb)

Произведён анализ и предварительная обработка датасета.

4. [*notebooks/algo_research.ipynb*](notebooks/algo_research.ipynb)

Выполнено исследование работы 14 алгоритмов машинного обучения (в т.ч. с использованием нейронных сетей) и выбрана лучшая модель - **настроенный XGBoost**.

5. [*src/main.py*](src/main.py)

Разработан бот для Telegram, который предсказывает уровень воды на постах, используя данные, которые предоставил пользователь и сервис [Gismeteo.Дневник](https://www.gismeteo.ru/diary/).

## Установка

    git clone https://github.com/phys-winner/water-predictor-bot
    cd water-predictor-bot
    git checkout
    py -m venv env
    .\env\Scripts\pip install -r requirements.txt

## Запуск
Перед первым запуском создайте файл **src\secret_auth.example.py** ([**пример**](src/secret_auth.example.py)) и укажите в нём логин и пароль от сайта АИС ГМВО, а также токен для бота Telegram.

    cd water-predictor-bot
    .\env\Scripts\python src\main.py

## Использованные данные и технологии

- [**АИС ГМВО**](https://gmvo.skniivh.ru/index.php?id=1) - данные о постах гидрологического контроля, а также ежедневные наблюдения за уровнем воды в реках;
- [**Gismeteo.Дневник**](https://www.gismeteo.ru/diary/) - архивные метео-данные.
- [**Википедия**](https://ru.wikipedia.org/wiki/%D0%97%D0%B0%D0%B3%D0%BB%D0%B0%D0%B2%D0%BD%D0%B0%D1%8F_%D1%81%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B0) - координаты населённых пунктов, в котором расположены посты контроля.
- **Python 3.9**
- **beautifulsoup4**
- **geopy**
- **htmlmin**
- **lxml**
- **matplotlib**
- **numpy**
- **pandas**
- **python-telegram-bot**
- **requests**
- **scikit-learn**
- **seaborn**
- **tensorflow**
- **xgboost**
- **xmltodict**

