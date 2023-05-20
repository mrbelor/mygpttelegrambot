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
button_menu5 = types.KeyboardButton("Очистить память бота у пользователя")
admmenu.add(button_menu1, button_menu2, button_menu3, button_menu4, button_menu5)

# Cancel markup
cancel = types.ReplyKeyboardMarkup(resize_keyboard = True)
button_cancel = types.KeyboardButton("Отмена") #создаём кнопку 
cancel.add(button_cancel) # пихаем кнопку

'''
def create_inline_Keyboard(button_name_list, button_callback_data_list):
	Keyboard = types.InlineKeyboardMarkup(row_width=2)
	for i in range(0, len(button_name_list)):
		button = types.InlineKeyboardButton(button_name_list[i], callback_data=button_callback_data_list[i])
		Keyboard.add(button)

	return Keyboard
'''

clear_inline_keyboard = types.InlineKeyboardMarkup(row_width=2)
button_inline_keyboard1 = types.InlineKeyboardButton('Очистить память бота', callback_data='clear') #создаём кнопку 
clear_inline_keyboard.add(button_inline_keyboard1) # пихаем кнопку

empty_markup = types.InlineKeyboardMarkup(row_width=2)

boolean = types.ReplyKeyboardMarkup(resize_keyboard = True)
button_boolean1 = types.KeyboardButton("Да")
button_boolean2 = types.KeyboardButton("Нет")
boolean.add(button_boolean1, button_boolean2)


'''
boolean_inline = types.InlineKeyboardMarkup(row_width=2)
button_boolean_inline1 = types.InlineKeyboardButton("Да", callback_data='Да')
button_boolean_inline2 = types.InlineKeyboardButton("Нет", callback_data='Нет')
boolean_inline.add(button_boolean_inline1, button_boolean_inline2)
'''