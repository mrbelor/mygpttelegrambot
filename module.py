import telebot, openai, datetime, sqlite3, traceback, tiktoken, re, os#, langdetect, googletrans==3.1.0a0

from telebot import types
from langdetect import detect as lang # для определения языка ввода
from googletrans import Translator

import config
import markup

users_sessions = {}
translator = Translator() # google translator
openai.api_key = config.OPENAI_T
bot = telebot.TeleBot(config.BOT_T)
#tik = tiktoken.get_encoding("cl100k_base")
tik = tiktoken.encoding_for_model(config.MODEL)

def menu(message):
    mrk = markup.menu
    if message.from_user.id == config.ADMIN:
        mrk = markup.admmenu

    bot.send_message(message.chat.id, "Меню", reply_markup = mrk)

def time(text = ""): # приписывает к тексту спереди дату
    if text:
        return str(datetime.datetime.now())[:-7] + "\n" + text + "\n"
    else:
        return str(datetime.datetime.now())[:-7]

def path(text):
    path_to_file = os.path.abspath(__file__)
    filename = os.path.basename(path_to_file)
    
    return path_to_file[:-len(filename)] + text

def list_token_counter(messages):
    tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
    tokens_per_name = -1

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += token_counter(value)
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens

def token_counter(item):
    return len(tik.encode(item))

def tr(text, targetlang = "ru"):
    tr = translator.translate(text, targetlang)
    return tr.text

def save_logs(log_item, reply=None):
    if reply:
        x = bot.reply_to(reply, time(log_item))
    else:
        x = bot.send_message(config.LOG_CHAT, text = time(log_item))
    print(time(log_item))
    return x


def clear_user(message):
    input_id = message.text
    if input_id == "Отмена":
        #return
        menu(message)
    else:
        db = sqlite3.connect(path("Bot3.5_DB.db")) # открытие базы данных
        c = db.cursor() # инициализация курсора
        c.execute("SELECT story FROM users WHERE id = ?", ([input_id]))
        story = c.fetchone()[0]
        db.close()
        
        if story == '[]':
            bot.send_message(message.chat.id, "Пустая история")
            #return
            menu(message)
        
        elif story:
            count = list_token_counter(eval(story))
            with open(path("story.txt"), "w", encoding="utf-8") as file:
                    txt = file.write(story)
            
            clear_session(input_id)
            
            f = open(path("story.txt"), "rb")
            bot.send_document(config.LOG_CHAT, f, caption=input_id+f'\nTokens: {str(count)}\nОчищено')
            f = open(path("story.txt"), "rb")
            bot.send_document(message.chat.id, f, caption=input_id+f'\nTokens: {str(count)}\nОчищено')

            menu(message)

        else:
            bot.send_message(message.chat.id, "не найдено  базе данных")
            #return
            menu(message)


def gpt(text, Id, session, username = 'User'):
    drop = None
    # sessions - словарь списков словарей
    # sessions - {Id:[{"role":"user", "content":text}, {"role":"assistant", "content":text}],
    #             Id:[{"role":"user", "content":text}, {"role":"assistant", "content":text}],
    #             Id:[{"role":"user", "content":text}, {"role":"assistant", "content":text}]}
    if not session:
        # Создание контекста
        session = [{"role":"system", "content":config.SYSTEM_MES.replace('username', username)}]
    
    # добавление пользовательского ввода в контекст для этого сеанса
    session.append({"role":"user", "content":text})
    # проверка на превышение
    count = list_token_counter(session)
    if count < 3_000:
        save_logs(str(count)+" токенов потрачено на запрос")
    else:

        reply = save_logs(f"Превышение допустимого количества токенов пользователем {username}, {Id}!\n(потеря информации)\ncount: {str(count)}")
        drop = True

        while count > 3_000:
            old_cout = count
            del session[1]
            count = list_token_counter(session)
            save_logs(f"Удаление {old_cout-count} токенов из истории {username}, {Id}\nlen(session) = {count}", reply)



    #sessions[Id] 

    x = openai.ChatCompletion.create(
        model = config.MODEL,
        # список словарей
        messages = session,
        max_tokens = 1000
        )

    answer = x['choices'][0]['message']['content']

    session.append({"role":"assistant", "content":answer})

    return answer, session, drop

def update_db(message):
    Id = message.from_user.id
    db = sqlite3.connect(path("Bot3.5_DB.db")) # открытие базы данных
    c = db.cursor() # инициализация курсора
    c.execute(f"UPDATE users SET username = ? WHERE id = {Id}", (['@'+str(message.from_user.username)]))
    c.execute(f"UPDATE users SET firstname = ? WHERE id = {Id}", ([message.from_user.first_name]))
    
    db.commit()
    db.close()

def clear_session(Id):
    db = sqlite3.connect(path("Bot3.5_DB.db")) # открытие базы данных
    c = db.cursor() # инициализация курсора

    #c.execute(f"UPDATE users SET story = ? WHERE id = {Id}", (["[]"]))
    #c.execute(f"UPDATE users SET story = ? WHERE id = ?", (["[]", Id]))
    c.execute("UPDATE users SET story = ? WHERE id = ?", ('[]', str(Id)))
    #c.execute(f"UPDATE users SET username = ? WHERE id = {Id}", (['@'+message.from_user.username]))
    db.commit()
    db.close()


def mess_for_admin(message):
    if message.text == "Отмена":
        menu(message)
    else:
        log_item = f'@mrbelor!\nCообщение от пользователя \n@{message.from_user.username}, {message.from_user.id}:\n"{message.text}"'
        save_logs(log_item)
        bot.send_message(config.ADMIN, time(log_item))
        bot.send_message(message.chat.id, "Сообщение отправлено, спасибо за обращение")
        menu(message)

def finder(message):
    if message.text == "Отмена":
        menu(message)
    
    else:
        db = sqlite3.connect(path("Bot3.5_DB.db")) # открытие базы данных
        c = db.cursor() # init курсор

        if message.text[0] == "@":
            c.execute("SELECT * FROM users WHERE username = ?", ([message.text]))
            what = 'username'
        elif message.text.isdigit():
            c.execute("SELECT * FROM users WHERE id = ?", ([message.text]))
            what = 'id'
        else:
            c.execute("SELECT * FROM users WHERE firstname = ?", ([message.text]))
            what = 'firstname'

        x = c.fetchall()
        if x:
            log_item = f"Найдено {len(x)} человек с {what}: {message.text}\n"
        else:
            log_item = f'Пользователя с {what}: {message.text} не удалось найти'

        db.commit()
        db.close()

        for i in x:
            #y = i[4].count("'role': 'user'")
            y = list_token_counter(eval(i[4]))
            log_item += (f"{i[2]}, {i[1]},\nid: {i[0]} , tokens: {y},\ndate: {i[3]}\n")

        bot.send_message(message.chat.id, log_item)
        save_logs(log_item)
        menu(message)



