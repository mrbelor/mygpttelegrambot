from telebot import types
import config

# Маркапы--------------------------------------------------------------------------
# menu
menu = types.ReplyKeyboardMarkup(resize_keyboard = True)
button_menu1 = types.KeyboardButton("Сделать запрос GPT")
button_menu2 = types.KeyboardButton("Написать администрации")
menu.add(button_menu1, button_menu2)

# adm menu
admmenu = types.ReplyKeyboardMarkup(resize_keyboard = True)
button_menu3 = types.KeyboardButton("Поиск пользователя") # с выводом всех его данных (id баланса и запросов)
button_menu4 = types.KeyboardButton("Написать от имени бота")
admmenu.add(button_menu1, button_menu2, button_menu3, button_menu4)

# Cancel markup
cancel = types.ReplyKeyboardMarkup(resize_keyboard = True)
button_cancel = types.KeyboardButton("Отмена") #создаём кнопку 
cancel.add(button_cancel) # пихаем кнопку

rest_menu = types.ReplyKeyboardMarkup(resize_keyboard = True)
button_rest_menu1 = types.KeyboardButton("старт▶") 
button_rest_menu2 = types.KeyboardButton("стоп❌")
rest_menu.add(button_rest_menu1, button_rest_menu2)

InlineClear = types.InlineKeyboardMarkup(row_width=2)
button_InlineClear1 = types.InlineKeyboardButton('Очистить память бота', callback_data='clear')