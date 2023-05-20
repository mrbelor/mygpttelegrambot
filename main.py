import telebot, openai, datetime, sqlite3, traceback, tiktoken, re#, langdetect, googletrans==3.1.0a0

from telebot import types
from langdetect import detect as lang # для определения языка ввода
from googletrans import Translator

import config, markup
from module import *

db = sqlite3.connect(path("Bot3.5_DB.db")) # открытие базы данных
c = db.cursor() # инициализация курсора
# создание бд, если её не существовало
c.execute("""CREATE TABLE IF NOT EXISTS users(
    id integer,
    username text,
    firstname text,
    join_date text,
    story text
)""")
db.commit()# обновление в базе данных
db.close() # закрытие базы данных

bot = telebot.TeleBot(config.BOT_T)
welcome_url = f'[зачем_нужен_ChatGPT.txt]({config.WELCOME_URL})'
instruct_url = f'[правильное_написание_запросов.txt]({config.INSTRUCT_URL})'

# Команды======================================================================================================================
@bot.message_handler(commands=['start'])
def start_comm(message):
    # Занос пользователя в базу данных
    db = sqlite3.connect(path("Bot3.5_DB.db")) # Открытие
    c = db.cursor() # инициализация курсора
    c.execute(f"SELECT id FROM users WHERE id = {message.chat.id}") # поиск в базе, и выбор при находе
    if c.fetchone():
        update_db(message)
        #clear_session(message)
        log_item = f"Пользователь @{message.from_user.username}, {message.from_user.id} нажал /start"
    else:
        x = [{"role":"system", "content":config.SYSTEM_MES.replace("username", message.from_user.first_name)}]
        x = str(x)
        c.execute("INSERT INTO users VALUES(?, ?, ?, ?, ?)", (message.from_user.id, '@'+str(message.from_user.username), message.from_user.first_name, time(), x))
        log_item = f"Новый пользователь!\nid: {message.from_user.id}\nusername: @{message.from_user.username}\nfirstname: {message.from_user.first_name}\n"
        
        db.commit()
        db.close()

    # логирование
    save_logs(log_item)

    # Преветствие
    #text = '[НАЖМИ](https://www.youtube.com/watch?v=dQw4w9WgXcQ)'
    #bot.send_message(message.chat.id, text+" ПОЖАЛУЙСТА", disable_web_page_preview = True, parse_mode='Markdown')
    bot.send_message(message.chat.id, f"Добро пожаловать, {message.from_user.first_name}!\nЯ {bot.get_me().first_name}. Я бот, сделаный на основе нейросети ChatGPT модели {config.MODEL}, который поможет вам в написании какой либо текстовой работы\n\nЧто такое ChatGPT и её возможности - "+welcome_url, disable_web_page_preview = True, parse_mode='Markdown')

    menu(message)

@bot.message_handler(commands=['clear'])
def cl(message):
    Id = message.from_user.id
    username = message.from_user.username

    clear_session(Id)
    save_logs(f'@{username}, {Id} очистил память gpt')
    
    bot.send_message(Id, 'Память успешно очищена.')

@bot.message_handler(commands=['drop'])
def test(message):
    if message.from_user.id == config.ADMIN:
        a = [1]
        print(a[1]) # вызов ошибки
    else:
        bot.send_message(message.chat.id, f"{message.from_user.username}, вы не можете использовать эту команду")

'''
@bot.message_handler(commands=['test'])
def test(message):
    if message.from_user.id == config.ADMIN:
        bot.send_message(message.chat.id, message)
    else:
        bot.send_message(message.chat.id, f"{message.from_user.username}, вы не можете использовать эту команду")
'''

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == 'clear':
        #save_logs(str(call))
        cl(call)
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup.empty_markup)
        # Делать что-то, когда нажимается кнопка 1
    elif call.data == 'translate':
        pass
        # Сделайте что-нибудь, когда нажата кнопка 2
    else:
        pass
        # Обработать другие нажатия на кнопку


# Обработка всех остальных сообщений============================================================================================
@bot.message_handler(content_types=['text'])
def msg(message):
    if message.text == "Сделать запрос GPT":
        next = bot.send_message(message.chat.id, "Введите текст запроса:\n\nнастоятельно рекомендуем к прочтению - " + instruct_url, disable_web_page_preview = True, parse_mode='Markdown', reply_markup = markup.cancel)
        bot.register_next_step_handler(message, gptrequest, next)

    elif message.text == "Написать администрации":
        bot.send_message(message.chat.id, "Введите текст сообщения администрации:\n\nкак можно подробно и чётко изложите суть своей проблемы, вопроса, или предложения\nВсе претензии по поводу качества ответов нейросети просьба посылать напрямую Создателю.", reply_markup = markup.cancel)
        bot.register_next_step_handler(message, mess_for_admin)

    elif message.from_user.id == config.ADMIN:
        if message.text == "Поиск пользователя":
            bot.send_message(message.chat.id, "Введите ID/username/firstname искомого пользователя", reply_markup = markup.cancel)
            bot.register_next_step_handler(message, finder)
        elif message.text == "Написать от имени бота":
            bot.send_message(message.chat.id, "Введите ID целевого пользователя", reply_markup = markup.cancel)
            bot.register_next_step_handler(message, text_to_user1)
        elif message.text == "Очистить память бота у пользователя":
            bot.send_message(message.chat.id, "Введите ID целевого пользователя", reply_markup = markup.cancel)
            bot.register_next_step_handler(message, clear_user)

        else:
            menu(message)
    elif message.text == "Отмена":
        menu(message)

    else:
        bot.register_next_step_handler(message, gptrequest)

# defs ===============================================================================================================

def gptrequest(message, next=None):
    if config.UPDATE_BD:
        update_db(message) # обновление

    db = sqlite3.connect(path("Bot3.5_DB.db")) # открытие базы данных
    c = db.cursor() # инициализация курсора
    c.execute("SELECT story FROM users WHERE id = ?", ([message.chat.id]))
    session = c.fetchone()[0]
    c.execute("SELECT id FROM users WHERE id = ?", ([message.chat.id]))
    x = c.fetchone()[0]
    
    
    if x: # если есть в базе данных
        if message.text == "Отмена" or message.text == "/start":
            db.close()
            menu(message)
        elif message.text == '/clear':
            cl(message)
            #save_logs(f"Пользователь @{message.from_user.username}, {message.from_user.id}\nИспользовал /clear")
            # уже есть логирование в cl()
        else:
            
            logs_text = message.text

            if message.text.isdigit() and lang(message.text) == "en":
                logs_trns = None
            else:
                # перевод message.text на английский и запись в message.text
                message.text = tr(message.text, "en")
                # Check4 (на всякий случай обрезка и здесь.)
                if len(message.text) > 3_000:
                    message.text = message.text[:3_000]
                
                logs_trns = message.text
                bot.reply_to(message, f'Перевод "{lang(logs_text)}"->"en"\n{logs_trns}')

            # логирование запроса
            if len(logs_text) < 2000 and (logs_trns is None or len(logs_trns) < 2000):
                log_send = save_logs(f'Запрос "{logs_text}"\nПеревод: "{logs_trns}"\nот @{message.from_user.username}, {message.from_user.id}\n')
            else:
                log_send = save_logs(f'Запрос "{logs_text}"')
                save_logs(f'Перевод: "{logs_trns}"')
                save_logs(f'от @{message.from_user.username}, {message.from_user.id}\n')


            # Сообщение об ожидании в переменной, для последующего удаления
            send = bot.reply_to(message, "Ожидание...")
            
            
            #print('ses:',session)
            # Запрос
            response, session = gpt(message.text, message.chat.id, eval(session), message.from_user.first_name)

            # + экстренная обрезка ответа
            if len(response) > 3_900:
                    message.text = message.text[:4_000]

            c.execute(f"UPDATE users SET story = ? WHERE id = {message.from_user.id}", ([str(session)]))
            db.commit()
            db.close()

            # перевод и перезапись в response_trns
            response_trns = tr(response)

            # логирование ответа
            log_item = f"\nОтвет: {response}\nдля @{message.from_user.username}, {message.from_user.id}\n"
            log_send = save_logs(log_item, log_send)

            save_logs(f"Перевод:\n{response_trns}", log_send)

            # пользователю
            bot.delete_message(message.chat.id, send.id) # удаление сообщения с ожиданием
            if next:
                bot.delete_message(message.chat.id, next.id) # удаление сообщения о следующем запросе
                
            send = bot.reply_to(message, response, reply_markup = markup.cancel) # ответ пользователю
            bot.reply_to(send, f"Перевод:\n{response_trns}")

            # дальше
            next = bot.send_message(message.chat.id, "Введите текст следующего запроса:\n\n"+ instruct_url, disable_web_page_preview = True, parse_mode='Markdown', reply_markup = markup.clear_inline_keyboard)
            bot.register_next_step_handler(message, gptrequest, next)



    else:
        bot.send_message(message.chat.id, "Ошибка. Вы не были найдены в базе.\nПереадресация на начало. Попробуйте снова, если видите это собщение в первый раз")
        start_comm(message)

# запуск мотора ####################################################################################
if not config.AUTO_RESTART:
    bot.polling(none_stop=True) # отключение автоподъёма

error, drop = None, None
while True:
    try:
        # Логи --------------------------------------------------------------------
        if drop:
            f = open(path("error_3.5.txt"), "rb")
            bot.send_document(config.LOG_CHAT, f, caption=drop)

            drop = None
            error = None
        else:
            save_logs("Запуск бота")
            #запуск=========================================================================
            bot.polling(none_stop=True)
    
    except Exception as e:
        if not error:
            drop = time("Бот упал")
            error = traceback.format_exc()

            print(drop)
            print(error)

            with open(path("error_3.5.txt"), "w", encoding="utf-8") as file:
                txt = file.write(drop + 'Ошибка:\n' + error)
