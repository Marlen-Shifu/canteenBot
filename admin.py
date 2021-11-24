from aiogram.types import Message
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import PASSWORD_FOR_ADMINS
from db import db_request


class AdminLoginState(StatesGroup):
    password = State()

class AddProductState(StatesGroup):
    name = State()
    price = State()
    photo = State()


async def is_admin(mes):
    try:
        conn, res = db_request('''
            SELECT * FROM admins WHERE id=(?)
        ''', [mes.from_user.id])

        if res.fetchone():
            return True
        else:
            await mes.answer('You are not logined as admin')
            return False
    except Exception as e:
        print(e)


async def im_admin(mes: Message):
    await mes.answer(f'Hello @{mes.from_user.username}\nEnter the password...')

    await AdminLoginState.password.set()


async def im_admin_password(mes: Message, state):
    if mes.text == PASSWORD_FOR_ADMINS:
        try:
            conn, res = db_request('''
                INSERT INTO admins VALUES(?,?)
            ''', (mes.from_user.id, mes.from_user.username))

            conn.commit()

            conn.close()

            await mes.answer('Login successfull\nNow you can write admin commands')

        except Exception as e:
            await mes.answer('You already logined and admin')

        await state.finish()

    else:
        await mes.answer(f'Error password')



async def add_product(mes: Message):
    await mes.answer('Enter name: ')

    await AddProductState.name.set()

async def add_product_name(mes: Message, state: FSMContext):
    await mes.answer('Enter price: ')

    await AddProductState.price.set()

    await state.update_data(name=mes.text)

async def add_product_price(mes: Message, state: FSMContext):
    await mes.answer('Send photo: ')

    await AddProductState.photo.set()

    await state.update_data(price=int(mes.text))

async def add_product_photo(mes: Message, state: FSMContext):

    try:

        data = await state.get_data()

        file_name = 'photos/' + data['name'] + '_photo.png'

        await mes.document.download(destination=file_name)


        conn, res = db_request('''
            INSERT INTO products(name, price, photo) VALUES(?,?,?)
        ''', [data['name'], data['price'], file_name])

        conn.commit()
        conn.close()

        await mes.answer('Product added')
    except Exception as e:
        print(e)
    finally:
        await state.finish()





def set_handlers_admin(dp):
    dp.register_message_handler(im_admin, commands=['im_admin'])

    dp.register_message_handler(im_admin_password, state=AdminLoginState.password)

    dp.register_message_handler(add_product, is_admin, commands=['add_product'])
    dp.register_message_handler(add_product_name, state=AddProductState.name)
    dp.register_message_handler(add_product_price, state=AddProductState.price)
    dp.register_message_handler(add_product_photo, state=AddProductState.photo, content_types=['document'])
