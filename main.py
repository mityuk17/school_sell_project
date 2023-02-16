import logging

from PyEasyQiwi import QiwiConnection

import db
from aiogram import Bot , Dispatcher , executor , types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State , StatesGroup
import config
QIWI_token = config.QIWI_token
conn = QiwiConnection(QIWI_token)
API_TOKEN = config.telegram_token
logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot , storage=storage)


class States(StatesGroup):
    get_amount = State()


@dp.message_handler(commands=[ 'start' ])
async def start(message: types.Message):
    db.create_user(message.chat.id)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Товары' , callback_data='show_products'))
    kb.add(types.InlineKeyboardButton(text='Корзина' , callback_data='show_korzina'))
    kb.add(types.InlineKeyboardButton(text='Пополнить баланс' , callback_data='balance'))
    kb.add(types.InlineKeyboardButton(text='Поддержка' , url=config.admin_link))
    await message.answer('Главное меню' , reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'main_menu')
async def menu(callback_query: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Товары' , callback_data='show_products'))
    kb.add(types.InlineKeyboardButton(text='Корзина' , callback_data='show_korzina'))
    kb.add(types.InlineKeyboardButton(text='Пополнить баланс' , callback_data='balance'))
    kb.add(types.InlineKeyboardButton(text='Поддержка' , url=config.admin_link))
    await callback_query.message.edit_text('Главное меню' , reply_markup=kb)

@dp.callback_query_handler(lambda query: query.data == 'balance')
async def refill_balance(callback_query: types.CallbackQuery):
    await States.get_amount.set()
    await callback_query.message.edit_text('Введите сумму, на которую хотите пополнить баланс:')
@dp.message_handler(state=States.get_amount)
async def create_payment(message: types.Message, state: FSMContext):
    amount = int(message.text)
    await state.finish()
    pay_url , bill_id , response = conn.create_bill(value=amount,
                                                    description=str(message.chat.id))
    db.create_payment(bill_id, message.chat.id, amount)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Проверить оплату', callback_data='check_payment_'+bill_id))
    await message.answer(f'''Перейдите по ссылке для оплаты:
{pay_url}''', reply_markup=kb)
@dp.callback_query_handler(lambda query: query.data.startswith('check_payment_'))
async def check_payment(callback_query : types.CallbackQuery):
    bill_id = callback_query.data.split('_')[ -1 ]
    status , response = conn.check_bill(bill_id)
    if status == 'PAID':
        await callback_query.message.edit_text(text='Оплата прошла успешно, деньги зачислены на ваш баланс', reply_markup=None)
        db.confirm_payment(bill_id, callback_query.message.chat.id)
    else:
        await callback_query.answer('Платёж не подтверждён.')
@dp.callback_query_handler(lambda query: query.data == 'show_products')
async def show_products(callback_query: types.CallbackQuery):
    company_names = db.get_company_names()
    kb = types.InlineKeyboardMarkup()
    for company in company_names:
        kb.add(types.InlineKeyboardButton(text=company , callback_data=f'company_{company}'))
    await callback_query.message.answer('Выберите производителя' , reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('company_'))
async def show_company_products(callback_query: types.CallbackQuery):
    company = callback_query.data.split('_')[ 1 ]
    kb = types.InlineKeyboardMarkup()
    products = db.get_company_products(company)
    for product in products:
        kb.add(types.InlineKeyboardButton(text=product[ 2 ] , callback_data=f'show_id_{product[ 0 ]}'))
    kb.add(types.InlineKeyboardButton(text='Назад' , callback_data='show_products'))
    await callback_query.message.edit_text(text=f'Выберите товар производителя {company}' , reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('show_id_'))
async def show_product(callback_query: types.CallbackQuery):
    product_id = callback_query.data.split('_')[ 2 ]
    product = db.get_product_by_id(int(product_id))
    product_id , company_name , model_name , price, description = product
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Добавить в корзину' , callback_data=f'add_korzina_{product_id}'))
    kb.add(types.InlineKeyboardButton(text='Вернуться назад' , callback_data=f'company_{company_name}'))
    text = f'''Название модели: {model_name}
Производитель: {company_name}
Цена: {price}'''
    text += '\n' + description
    await callback_query.message.edit_text(text , reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('add_korzina_'))
async def add_korzina(callback_query: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Меню', callback_data='main_menu'))
    product_id = int(callback_query.data.split('_')[ 2 ])
    db.add_product_to_korzina(product_id , callback_query.message.chat.id)
    await callback_query.message.edit_text(text='Продукт успешно добавлен в корзину' , reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'show_korzina')
async def show_korzina(callback_query: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Оплатить корзину', callback_data='buy_korzina'))
    kb.add(types.InlineKeyboardButton(text='Очистить корзину', callback_data='clear_korzina'))
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='main_menu'))
    korzina_txt = db.create_korzina_txt(callback_query.message.chat.id)
    user = db.get_user(callback_query.message.chat.id)
    balance = user[ 1 ]
    korzina = user[ 2 ]
    cost = 0
    for product_id in korzina.split():
        product = db.get_product_by_id(int(product_id))
        price = product[ 3 ]
        cost += price
    text = f'''Ваш баланс: {balance}
Стоимость корзины: {cost}
Ваша корзина:
'''
    text += korzina_txt
    await callback_query.message.edit_text(text=text, reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'clear_korzina')
async def clear_korzina(callback_query: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Меню', callback_data='main_menu'))
    db.clean_korzina(callback_query.message.chat.id)
    await callback_query.message.edit_text('Корзина очищена', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'buy_korzina')
async def buy_korzina(callback_query: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text= 'Меню', callback_data='main_menu'))
    user = db.get_user(callback_query.message.chat.id)
    balance = user[1]
    korzina = user[2]
    if not korzina:
        await callback_query.message.edit_text('Корзина пуста', reply_markup=kb)
        return
    cost = 0
    for product_id in korzina.split():
        product = db.get_product_by_id(int(product_id))
        price = product[3]
        cost += price
    if cost > balance:
        await callback_query.message.edit_text('Недостаточно средств на балансе', reply_markup=kb)
        return
    await callback_query.message.edit_text('''Покупка прошла успешно.
Ожидайте сообщение от администратора.''', reply_markup=kb)
    user_link = await callback_query.message.chat.get_url()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Написать покупателю', url=user_link))
    text = f'''Пользователь {callback_query.message.chat.username} оплатил покупку
В заказ входит:
'''
    korzina_txt = db.create_korzina_txt(callback_query.message.chat.id)
    text += korzina_txt
    await bot.send_message(chat_id = config.admin_id, text=text)
    db.spend_balance(callback_query.message.chat.id, cost)
    db.clean_korzina(callback_query.message.chat.id)

if __name__ == '__main__':
    db.start()
    executor.start_polling(dp , skip_updates=True)
