from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message, InputFile, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup

from db import db_request

from config import SELLERS_ID


start_markup = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('/offer'))


menu_markup = ReplyKeyboardMarkup(resize_keyboard=True)

btn_send_offer = KeyboardButton('Send Offer')
btn_cart = KeyboardButton('View Cart')
btn_cancel = KeyboardButton('Cancel')

menu_markup.add(btn_send_offer)
menu_markup.add(btn_cart)
menu_markup.add(btn_cancel)


yes_no_markup = ReplyKeyboardMarkup(resize_keyboard=True)
btn_yes = KeyboardButton('Yes')
btn_no = KeyboardButton('No')

yes_no_markup.add(btn_yes, btn_no)

class OfferState(StatesGroup):
    cart = State()

    count = State()
    confirm_add_to_cart = State()

    name = State()
    confirm_send_offer = State()





async def start(mes: Message):
    await mes.answer(f'Hello @{mes.from_user.username}\nYou can offer kantin by this bot  for not waiting...', reply_markup=start_markup)

    try:
        conn, res = db_request('''
            INSERT INTO registered_users VALUES(?,?)
        ''', (mes.from_user.id, mes.from_user.username))

        conn.commit()

        conn.close()
    except Exception as e:
        print(e)


async def offer(mes: Message):



    await mes.answer(f'Choose of them...', reply_markup=menu_markup)

    conn, res = db_request('''
        SELECT * FROM products
    ''')

    products = res.fetchall()

    conn.close()

    await OfferState.cart.set()

    for product in products:
        photo = InputFile(product[3])

        markup = InlineKeyboardMarkup()
        btn_add = InlineKeyboardButton('Add to cart', callback_data=product[0])

        markup.add(btn_add)

        await mes.answer_photo(photo=photo, caption=f'Name: {product[1]}\nPrice: {product[2]}тг', reply_markup=markup)


async def choosen_product(call: CallbackQuery, state: FSMContext):
    await state.update_data(choosen_product=call.data)

    await OfferState.count.set()

    await call.bot.send_message(call.from_user.id, 'Enter count')

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

        await mes.answer(f'Do you confirm this info?\nName: {product_info["name"]}\nCount: {product_info["count"]}', reply_markup=yes_no_markup)

    except Exception as e:
        await mes.answer('Enter integer number')

async def confirm_add_to_cart(mes: Message, state: FSMContext):
    if mes.text == 'Yes':
        data = await state.get_data()

        try:
            before_info = data['products_list']
        except KeyError as e:
            before_info = []

        before_info.append(data['product_info'])

        await state.update_data(products_list=before_info)

        await OfferState.cart.set()

        await mes.answer('Select other or send offer', reply_markup=menu_markup)
    elif mes.text == 'No':
        await OfferState.cart.set()

        await mes.answer('Select other or send offer', reply_markup=menu_markup)
    else:
        await mes.answer('Type "Yes" or "No"')


async def send_offer_handler(mes:Message, state:FSMContext):
    data = await state.get_data()

    try:
        products_info = data['products_list']
    except KeyError as e:
        await mes.answer('No product in cart')
        return

    await OfferState.name.set()

    await mes.answer('Write your name by which seller will call you')

async def confirm_send_offer(mes:Message, state:FSMContext):

    data = await state.get_data()

    try:
        products_info = data['products_list']
    except KeyError as e:
        await mes.answer('No product in cart')
        return

    await state.update_data(name=mes.text)

    await OfferState.confirm_send_offer.set()

    await mes.answer(f'Do you confirm send your offer?\n{products_info}\nName: {mes.text}', reply_markup=yes_no_markup)


async def send_offer(mes: Message, state: FSMContext):
    if mes.text == 'Yes':
        data = await state.get_data()

        try:
            products_info = data['products_list']
            name = data['name']
        except KeyError as e:
            info = []


        for seller_id in SELLERS_ID:
            await mes.bot.send_message(seller_id, f'New offer:\n{products_info}\nName: {name}')

        await state.finish()

        await mes.answer(f'Your offer sent\n{products_info}\nName: {name}', reply_markup=start_markup)

    elif mes.text == 'No':
        await OfferState.cart.set()

        await mes.answer('Select other or send offer', reply_markup=menu_markup)

    else:
        await mes.answer('Type "Yes" or "No"')


async def view_cart(mes:Message, state:FSMContext):
    data = await state.get_data()

    try:
        products_info = data['products_list']
    except KeyError as e:
        products_info = []

    await mes.answer(str(products_info))


async def cancel_offer(mes: Message, state: FSMContext):
    await mes.answer('Cancel offer', reply_markup=ReplyKeyboardMarkup().add(KeyboardButton('/offer')))
    await state.finish()





def set_handlers_user(dp):
    dp.register_message_handler(start, commands=['start'])
    dp.register_message_handler(offer, commands=['offer'])

    dp.register_message_handler(cancel_offer, lambda m: m.text == 'Cancel', state=OfferState.cart)

    dp.register_message_handler(view_cart, lambda m: m.text == 'View Cart', state=OfferState.cart)

    dp.register_message_handler(send_offer_handler, lambda m: m.text == 'Send Offer', state=OfferState.cart)
    dp.register_message_handler(confirm_send_offer, state=OfferState.name)
    dp.register_message_handler(send_offer, state=OfferState.confirm_send_offer)

    dp.register_callback_query_handler(choosen_product, state=OfferState.cart)
    dp.register_message_handler(product_count, state=OfferState.count)
    dp.register_message_handler(confirm_add_to_cart, state=OfferState.confirm_add_to_cart)

