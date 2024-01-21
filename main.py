import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import executor

API_TOKEN = os.getenv("TOKEN")  # Замените на свой токен
CHAT_ID = os.getenv("CHAT_ID") # ID вашего чата

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


class Form(StatesGroup):
    Start = State()
    Photos = State()
    Date = State()
    InvoiceNumber = State()
    Supplier = State()
    Location = State()
    Amount = State()
    Confirm = State()





@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Прислать накладную"))

    await message.reply(f"Привет! {message.from_user.first_name} Этот бот поможет вам отправить информацию в другой чат.", reply_markup=keyboard)
    await message.reply(text="Для начала воспользуйтесь кнопкой 'Прислать накладную'.",
                           reply_markup=keyboard)

@dp.message_handler(lambda message: message.text.lower() == 'прислать накладную', state='*')
async def send_invoice(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply("Хорошо! Теперь пришлите фотографии накладной (1/2/3), по одной.")
    await Form.Photos.set()


@dp.message_handler(commands=['skip'], state=Form.Photos)
async def skip_photos(message: types.Message, state: FSMContext):
    await message.reply("Вы решили пропустить отправку фотографий. Теперь введите дату в формате 13/04/2022:")
    await Form.next()


@dp.message_handler(content_types=['photo'], state=Form.Photos)
async def process_photos(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if 'photos' not in data:
            data['photos'] = []

        data['photos'].append(message.photo[-1].file_id)

        if len(data['photos']) < 3:
            await message.reply(f"Фотография {len(data['photos'])} принята. Пришлите еще фотографию "
                                f"Вы также можете воспользоваться командой /skip для пропуска этого шага:")
        else:
            await message.reply("Все фотографии приняты. Теперь введите дату в формате 13/04/2022:")
            await Form.next()


@dp.message_handler(state=Form.Date)
async def process_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['date'] = message.text

    await Form.next()
    await message.reply("Введите номер накладной:")


@dp.message_handler(state=Form.InvoiceNumber)
async def process_invoice(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['invoice_number'] = message.text

    await Form.next()
    await message.reply("Введите поставщика:")


@dp.message_handler(state=Form.Supplier)
async def process_supplier(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['supplier'] = message.text

    await Form.next()
    await message.reply("Введите точку:")


@dp.message_handler(state=Form.Location)
async def process_location(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['location'] = message.text

    await Form.next()
    await message.reply("Введите сумму:")


@dp.message_handler(state=Form.Amount)
async def confirm_information(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['amount'] = message.text

        info_message = f"Дата: {data['date']}\nНомер накладной: {data['invoice_number']}\n" \
                       f"Поставщик: {data['supplier']}\nТочка: {data['location']}\nСумма: {data['amount']}"

        media = [InputMediaPhoto(media_id) for media_id in data['photos']]
        await bot.send_media_group(chat_id=CHAT_ID, media=media)
        await bot.send_message(chat_id=CHAT_ID, text=info_message, parse_mode=ParseMode.MARKDOWN)

        await message.reply("Информация и фотографии отправлены в другой чат.")
        await state.finish()  # Сброс состояния и данных
        await message.reply("Для начала воспользуйтесь кнопкой 'Прислать накладную'.")


if __name__ == '__main__':
    # Запуск бота
    executor.start_polling(dp, skip_updates=True)
