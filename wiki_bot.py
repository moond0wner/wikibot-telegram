"""Бот на Python, который помогает находить информацию из Википедии прямо в телеграм. Version (1.0)
Основной функционал готов, планируется добавить дополнительный функционал:
1. Поиск изображений по запросу.
2. Получение новостей и обновлений из Википедии.
3. Возможность поменять язык интерфейса. (Английский и немецкий)
"""

import wikipedia
import requests
import telebot
import time
import os
from PIL import Image

TOKEN = 'YOUR_TOKEN'
bot = telebot.TeleBot(TOKEN)
wikipedia.set_lang('ru')  # по умолчанию

filename = 'articles.txt'

# Кнопки для /search
keyboard1 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard1.row("Найти ещё одну статью", "Найти случайную статью", "Просмотреть историю статей", "Вернуться к началу")

# Кнопки для /random_article
keyboard2 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard2.row("Найти ещё одну случайную статью", "Найти статью по теме", "Просмотреть историю статей", "Вернуться к началу")

# Удаление клавиатуры
keyboard3 = telebot.types.ReplyKeyboardRemove()

# Кнопки для /search_image
keyboard4 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard4.row("Попробовать еще раз", "Вернуться к начачу")

# Старт, список команд
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет, я бот, который поможет пользователям получать информацию из Википедии "
                                      "прямо в чате. "
                                      "Пользователь сможет отправлять запросы и получать краткую информацию о любой теме,"
                                      " человеке, месте и т.д. из Википедии."
                                      "\nСписок команд бота:\n/start - запустить бота."
                                      "\n/search - найти статью по вашей теме."
                                      "\n/search_image - найти картинку по вашей теме. (хуйня не работает)"
                                      "\n/choose_lang - выбрать язык на котором будет написана статья (по умолчанию русский). "
                                      "\n/history_articles - просмотреть историю запрашиваемых вами статей."
                                      "\n/random_article - получить случайную статью. "
                                      "\n/clear_history - очистить историю статей.", reply_markup=keyboard3)

# Поиск статьи по теме
@bot.message_handler(commands=['search'])
def handle_search1(message):
    bot.send_message(message.chat.id, "Введите тему по которой тебе нужно найти статью.")
    bot.register_next_step_handler(message, handle_search2)

def handle_search2(message):
    global search_results
    title = message.text
    try:
        search_results = wikipedia.search(title, results=5)
        show_result = ''
        bot.send_message(message.chat.id, "Найдены следующие статьи:\n")
        for i, article_title in enumerate(search_results, 1):
            show_result += f'\n{i}. {article_title}'
        bot.send_message(message.chat.id, show_result)
        bot.send_message(message.chat.id, "Выберите нужную вам статью")

        def get_article(message):
            index = int(message.text) - 1
            result = wikipedia.summary(search_results[index])
            get_url = wikipedia.page(search_results[index])
            get_url = get_url.url
            result += "\nСсылка на полную статью: \n" + get_url
            bot.send_message(message.chat.id, result)

            if os.path.exists(filename) and os.stat(filename).st_size > 0:
                write_mode = 'a'
            else:
                write_mode = 'w'

            with open(filename, write_mode) as file:
                if write_mode == 'w':
                    file.write(search_results[index] + ': ' + get_url)
                else:
                    file.write('\n' + search_results[index] + ': ' + get_url)
            bot.send_message(message.chat.id,"Статья сохранена", reply_markup=keyboard1)

        bot.register_next_step_handler(message, get_article)

    except wikipedia.exceptions.PageError as e:
        bot.send_message(message.chat.id, "Обработана ошибка неоднозначности!")
        bot.send_message(message.chat.id, f"Найдено несколько значений для темы {title}:\n")
        show_result = ''
        for i, res in enumerate(search_results, 1):
            show_result += f'{i}. {res}'
        bot.send_message(message.chat.id, show_result + '\nПожалуйста уточните в следующий раз тему.')
        time.sleep(2)
        handle_search1(message)

    except wikipedia.exceptions.PageError:
        # Обработка ошибки, когда статья не найдена
        bot.send_message(message.chat.id, f"Статья по теме '{title}' не найдена.")




@bot.message_handler(commands=['search_image']) # РАБОТАЕТ НИХУЯ
def handle_search_image(message):
    bot.send_message(message.chat.id, "Введите тему по которой тебе нужно найти картинку.")

    def get_image(message):
        """
           Принимает тему от пользователя, находит соответствующую статью в Wikipedia
           и отправляет ссылку на первую найденную в ней картинку.
           """
        try:
            # Получаем страницу Wikipedia по заданной теме
            topic = message.text
            page = wikipedia.page(topic)
            image_url = page.images[0]

            # Загружаем изображение с URL-адреса
            response = requests.get(image_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0'})

            # Проверяем, что изображение загрузилось успешно
            if response.status_code == 200:
                # Сохраняем изображение на диск
                filename = f"{topic.replace(' ', '_')}.png"
                with open(filename, "wb") as f:
                    f.write(response.content)

                # Отправляем изображение в Telegram-бот
                with open(filename, "rb") as f:
                    bot.send_photo(message.chat.id, f)
            else:
                bot.send_message(message.chat.id, "Ошибка при загрузке изображения.")
        except Exception as e:
            bot.send_message(message.chat.id, f"Произошла ошибка: {e}")
        finally:
            # Удаляем временный файл
            os.remove(filename)

    bot.register_next_step_handler(message, get_image)

@bot.message_handler(commands=['choose_lang'])
def handle_choose_language(message):
    bot.send_message(message.chat.id, "Напишите префикс того языка который вы хотите выбрать: "
                                      "\nРусский (ru)"
                                      "\nАнглийский (en)"
                                      "\nНемецкий (de)"
                                      "\nФранцузский (fr)")
    bot.register_next_step_handler(message, handle_choose_language_cont)
def handle_choose_language_cont(message):
    lang_lst = {'ru': "Русский", 'en': "Английский", 'de': "Немецкий", 'fr': "Французский"}
    language = message.text
    wikipedia.set_lang(language)
    bot.send_message(message.chat.id, f'Выбран язык: {lang_lst[language]}', reply_markup=keyboard1)

@bot.message_handler(commands=['history_articles'])
def handle_history_articles(message):
    try:
        with open ('articles.txt', 'r') as file:
            articles = file.readlines()
            if articles:
                article_list = ''
                for i, article in enumerate(articles, 1):
                    article_list += f'{i}. {article}'
                bot.send_message(message.chat.id, f'Предоставляю список статей, которые вы запрашивали: \n{article_list}')
            else:
                bot.send_message(message.chat.id, 'Ваш список cтатей пока пуст!')
    except FileNotFoundError:
        bot.send_message(message.chat.id, 'Ваш список статей пока пуст.')



@bot.message_handler(commands=['random_article'])
def handle_random_article(message):
    try:
        bot.send_message(message.chat.id, "Я отыщу для вас статью наугад.")

        time.sleep(3)

        # Получить случайный заголовок статьи
        random_article = wikipedia.random()

        # Получить содержимое случайной статьи
        page = wikipedia.page(random_article)

        title = page.title
        get_url = page.url
        result = page.summary

        bot.send_message(message.chat.id, result + '\nСсылка на полную статью: ' + get_url)

        if os.path.exists(filename) and os.stat(filename).st_size > 0:
            write_mode = 'a'
        else:
            write_mode = 'w'

        with open(filename, write_mode) as file:
            if write_mode == 'w':
                file.write(title + ': ' + get_url)
            else:
                file.write('\n' + title + ': ' + get_url)

        time.sleep(2)
        bot.send_message(message.chat.id, "Статья сохранена. \nДля просмотра истории статей напишите /history_articles", reply_markup=keyboard2)
    except Exception as e:
        bot.send_message(message.chat.id, f'Обработана ошибка: {e}. \nПопробуйте еще раз.', reply_markup=keyboard2)


@bot.message_handler(commands=['clear_history'])
def handle_clear_history_articles(message):
    bot.send_message(message.chat.id, "Провожу проверку списка...")
    time.sleep(3)
    if os.path.exists(filename) and os.stat(filename).st_size > 0:
        with open(filename, 'w') as file:
            file.write('')
        bot.send_message(message.chat.id, "Список очищен!")
    else:
        bot.send_message(message.chat.id, "Тут нечего чистить! Ваш список пуст.")

@bot.message_handler(content_types=['text'])
def handler(message):
    if message.text == "Найти ещё одну статью":
        time.sleep(5)
        handle_search1(message)
    elif message.text == "Найти ещё одну случайную статью":
        time.sleep(5)
        handle_random_article(message)
    elif message.text == "Найти случайную статью":
        handle_random_article(message)
    elif message.text == "Найти статью по теме":
        handle_search1(message)
    elif message.text == "Просмотреть историю статей":
        handle_history_articles(message)
    elif message.text == "Попробовать еще раз":
        time.sleep(5)
        handle_search_image(message)
    elif message.text == "Вернуться к началу":
        bot.send_message(message.chat.id, "Возвращаемся к начальному меню...", reply_markup=keyboard3)
        time.sleep(3)
        handle_start(message)


bot.infinity_polling()
