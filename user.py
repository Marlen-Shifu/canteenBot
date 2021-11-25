from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message, InputFile, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup

from db import db_request

from config import SELLERS_ID


start_markup = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Заказать'))


menu_markup = ReplyKeyboardMarkup(resize_keyboard=True)

btn_send_offer = KeyboardButton('Отправить заказ')
btn_cart = KeyboardButton('Корзина')
btn_cancel = KeyboardButton('Отмена')

menu_markup.add(btn_send_offer)
menu_markup.add(btn_cart)
menu_markup.add(btn_cancel)


yes_no_markup = ReplyKeyboardMarkup(resize_keyboard=True)
btn_yes = KeyboardButton('Да')
btn_no = KeyboardButton('Нет')

yes_no_markup.add(btn_yes, btn_no)

class OfferState(StatesGroup):
    cart = State()

    count = State()
    confirm_add_to_cart = State()

    name = State()
    confirm_send_offer = State()


async def data_to_readable_string(data: list):

    string = 'Товары:'

    total_price = 0

    for product in data:
        string += f'\n    Название: {product["name"]}\n    Цена: {product["price"]}\n    Количество: {product["count"]}\n    Сумма: {int((product["price"] * product["count"]) * 1.1)}\n'
        total_price += int((product["price"] * product["count"]) * 1.1)

    string += f'\nОбщая сумма: {total_price}тг'

    return string


async def start(mes: Message):
    await mes.answer(f'Привет @{mes.from_user.username}\nВы можеште через этого бота заказать из кантина с доставкой', reply_markup=start_markup)

    try:
        conn, res = db_request('''
            INSERT INTO registered_users VALUES(?,?)
        ''', (mes.from_user.id, mes.from_user.username))

        conn.commit()

        conn.close()
    except Exception as e:
        print(e)


async def offer(mes: Message):



    await mes.answer(f'Выберите один из товаров', reply_markup=menu_markup)

    conn, res = db_request('''
        SELECT * FROM products
    ''')

    products = res.fetchall()

    conn.close()

    await OfferState.cart.set()

    for product in products:
        photo = InputFile(product[3])

        markup = InlineKeyboardMarkup()
        btn_add = InlineKeyboardButton('Добавить в корзину', callback_data=product[0])

        markup.add(btn_add)

        await mes.answer_photo(photo=photo, caption=f'Название: {product[1]}\nЦена: {product[2]}тг', reply_markup=markup)


async def choosen_product(call: CallbackQuery, state: FSMContext):
    await state.update_data(choosen_product=call.data)

    await OfferState.count.set()

    await call.bot.send_message(call.from_user.id, 'Введите количество')

async def product_count(mes: Message, state: FSMContext):
    try:
        count = int(mes.text)

        data = await state.get_data()

        conn, res = db_request('''
            SELECT * FROM products WHERE id=(?)
        ''', data['choosen_product'])

        product_data = res.fetchone()

        product_info = {'name': product_data[1], 'price': product_data[2], 'count': count}

        await state.update_data(product_info=product_info)


        await OfferState.confirm_add_to_cart.set()

        await mes.answer(f'Вы подтверждаете?\nНазвание: {product_info["name"]}\nКоличество: {product_info["count"]}', reply_markup=yes_no_markup)

    except Exception as e:
        await mes.answer('Введите целое число')

async def confirm_add_to_cart(mes: Message, state: FSMContext):
    if mes.text == 'Да':
        data = await state.get_data()

        try:
            before_info = data['products_list']
        except KeyError as e:
            before_info = []

        before_info.append(data['product_info'])

        await state.update_data(products_list=before_info)

        await OfferState.cart.set()

        await mes.answer('Выберите еще или отправьте заказ', reply_markup=menu_markup)
    elif mes.text == 'Нет':
        await OfferState.cart.set()

        await mes.answer('Выберите еще или отправьте заказ', reply_markup=menu_markup)
    else:
        await mes.answer('Введите "Да" или "Нет"')


async def send_offer_handler(mes:Message, state:FSMContext):
    data = await state.get_data()

    try:
        products_info = data['products_list']
    except KeyError as e:
        await mes.answer('No product in cart')
        return

    await OfferState.name.set()

    await mes.answer('Введите имя по которому вас определят')

async def confirm_send_offer(mes:Message, state:FSMContext):

    data = await state.get_data()

    try:
        products_info = data['products_list']
    except KeyError as e:
        await mes.answer('Нет товаров в корзине')
        return

    await state.update_data(name=mes.text)

    await OfferState.confirm_send_offer.set()

    await mes.answer(f'Подтверждаете ли вы заказ?\n{await data_to_readable_string(products_info)}\nИмя: {mes.text}', reply_markup=yes_no_markup)


async def send_offer(mes: Message, state: FSMContext):
    if mes.text == 'Да':
        data = await state.get_data()

        try:
            products_info = data['products_list']
            name = data['name']
        except KeyError as e:
            info = []


        for seller_id in SELLERS_ID:
            await mes.bot.send_message(seller_id, f'Новый заказ:\n{await data_to_readable_string(products_info)}\nИмя: {name}')

        await state.finish()

        await mes.answer(
            'Ваш заказ отправлен', reply_markup=start_markup)

    elif mes.text == 'Нет':
        await OfferState.cart.set()

        await mes.answer('Добавьте другой товар или отправьте заказ', reply_markup=menu_markup)

    else:
        await mes.answer('Введите "Да" или "Нет"')


async def view_cart(mes:Message, state:FSMContext):
    data = await state.get_data()

    try:
        products_info = data['products_list']
    except KeyError as e:
        products_info = []

    await mes.answer(f'Корзина'
                     f'\n{await data_to_readable_string(products_info)}')


async def cancel_offer(mes: Message, state: FSMContext):
    await mes.answer('Заказ отменен', reply_markup=ReplyKeyboardMarkup().add(KeyboardButton('Заказать')))
    await state.finish()





def set_handlers_user(dp):
    dp.register_message_handler(start, commands=['start'])
    dp.register_message_handler(offer, lambda m: m.text == 'Заказать')

    dp.register_message_handler(cancel_offer, lambda m: m.text == 'Отмена', state=OfferState.cart)

    dp.register_message_handler(view_cart, lambda m: m.text == 'Корзина', state=OfferState.cart)

    dp.register_message_handler(send_offer_handler, lambda m: m.text == 'Отправить заказ', state=OfferState.cart)
    dp.register_message_handler(confirm_send_offer, state=OfferState.name)
    dp.register_message_handler(send_offer, state=OfferState.confirm_send_offer)

    dp.register_callback_query_handler(choosen_product, state=OfferState.cart)
    dp.register_message_handler(product_count, state=OfferState.count)
    dp.register_message_handler(confirm_add_to_cart, state=OfferState.confirm_add_to_cart)

