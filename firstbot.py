import config
import logging
import asyncio
import random
import time

from d3_parser import D3
from nhc_parser import NHC
from python_articles import PyArticles
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# задаем уровень логов
logging.basicConfig(level=logging.INFO)

# инициализируем бота
bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(bot)

# для ответа на сообщения от собеседника, генерируем список стикеров
# список стикер-наборов от Павла Дурова
durov_top50_stickersets = ['RickAndMorty', 'HotCherry', 'TheLittleMole', 'TextAnimated', 'ChristmasOrnaments']


# выбираем случайный стикер
async def random_sticker():
    StickerSet = await bot.get_sticker_set(random.choice(durov_top50_stickersets))
    sticker = random.randrange(len(StickerSet.stickers))
    return dict(StickerSet['stickers'][sticker]).get('file_id')

# инициализируем парсинг лучших статей с д3 за day, week, month, year
d3 = D3()

# инициализируем парсинг состояния циклонов в регионе
nhc = NHC('last_hurricane_info.txt')

# инициализируем парсинг новых статей о Python
pypubs = PyArticles('python_last.txt')


# отправляем сообщение, если есть изменения в циклонах
async def nhc_scheduled(wait_for):
    # ======================================== LOGGING ========================================
    logging.info(f"Запускаем поиск циклонов")

    while True:
        await asyncio.sleep(wait_for)

        # проверяем статус циклонов
        status = nhc.status_check()

        if status != nhc.alert_text:
            message_alert = nhc.alert_message()
            inline_kb = InlineKeyboardMarkup()
            if message_alert[1]:
                inline_kb.add(InlineKeyboardButton('Открыть Атлантический регион', url='https://www.nhc.noaa.gov/cyclones/?atlc'))
            elif message_alert[2]:
                inline_kb.add(InlineKeyboardButton('Открыть Тихий океан', url='https://www.nhc.noaa.gov/cyclones/?epac'))
            # отправляем 1-ый стикер
            file_id = await random_sticker()
            await bot.send_sticker(chat_id='789561316', sticker=file_id)
            # await bot.send_sticker(chat_id='822653560', sticker=file_id)

            await bot.send_message(text=message_alert[0], chat_id='789561316', parse_mode='HTML', reply_markup=inline_kb)
            # await bot.send_message(text=message_alert[0], chat_id='822653560', parse_mode='HTML', reply_markup=inline_kb)

            # обновляем информацию о циклонах в файле
            nhc.update_hurricanes_info(status)


# отправляем новые статьи о питоне
async def python_articles_scheduled(wait_for):
    # ======================================== LOGGING ========================================
    logging.info(f"Получаем новые статьи о Python")

    while True:
        await asyncio.sleep(wait_for)

        articles_list = pypubs.parse_new()
        if articles_list:
            for art in articles_list:
                time.sleep(random.randrange(20, 60))
                inline_kb = InlineKeyboardMarkup()
                inline_kb.add(InlineKeyboardButton(f"open {str(art['post_title']).upper()}...</b>", url=art['post_link']))
                await bot.send_message(789561316, f"{art['post_title']}   {art['post_link']}", parse_mode='HTML', reply_markup=inline_kb)
            await bot.send_message(789561316, f"total: {len(articles_list)}", parse_mode='HTML')
        else:
            await bot.send_message(789561316, "no new articles", parse_mode='HTML')


@dp.message_handler(regexp='(^d3|dirty)')
async def d3_scheduled(message: types.Message):

    num = str(message.text).replace('d3 ', '').replace('dirty ', '').replace('d3', '').replace('dirty', '')
    quantity = int(num) if num.isnumeric() else None

    # получаем список публикаций и отправляем по одному
    d3_publications = d3.new_articles_d3(quantity)
    for pub in d3_publications:
        await bot.send_message(text=pub['link'], chat_id='789561316')


@dp.message_handler(regexp='(^ураган[ы]?$|шторм[ы]?$|циклон[ы]?$)')
async def hurrican(message: types.Message):

    message_alert = nhc.alert_message()
    inline_kb = InlineKeyboardMarkup()
    if message_alert[1]:
        inline_kb.add(InlineKeyboardButton('Открыть Атлантический регион', url='https://www.nhc.noaa.gov/cyclones/?atlc'))
    elif message_alert[2]:
        inline_kb.add(InlineKeyboardButton('Открыть Тихий океан', url='https://www.nhc.noaa.gov/cyclones/?epac'))
    await message.reply(message_alert[0], parse_mode='HTML', reply_markup=inline_kb)


@dp.message_handler(regexp='(^python?$|питон?$)')
async def latest_python_pubs(message: types.Message):

    articles_list = pypubs.parse_new()
    if articles_list:
        for art in articles_list:
            time.sleep(random.randrange(20, 60))
            inline_kb = InlineKeyboardMarkup()
            inline_kb.add(InlineKeyboardButton(f"open {str(art['post_title']).upper()}...", url=art['post_link']))
            await bot.send_message(789561316, f"{art['post_title']}   {art['post_link']}", parse_mode='HTML', reply_markup=inline_kb)
        await bot.send_message(789561316, f"total: {len(articles_list)}", parse_mode='HTML')
    else:
        await bot.send_message(789561316, "no new articles", parse_mode='HTML')


@dp.message_handler()
async def echo(message: types.Message):
    file_id = await random_sticker()
    await message.answer_sticker(file_id)
    await message.answer_dice()
    # await message.answer(message.text)





# запускаем лонг поллинг
if __name__ == '__main__':
    dp.loop.create_task(python_articles_scheduled(60))  # пока что оставим 10 секунд (в качестве теста)
    dp.loop.create_task(nhc_scheduled(12*60*60))  # пока что оставим 10 секунд (в качестве теста)
    # dp.loop.create_task(d3_scheduled(60*60*6))  # пока что оставим 10 секунд (в качестве теста)
    executor.start_polling(dp, skip_updates=True)
