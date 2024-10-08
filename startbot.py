import asyncio
import sys
import logging
from os import getenv
from datetime import datetime
from dotenv import load_dotenv


from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message


from periodic import periodic
from db import (
    create_db_and_tables, create_infobase_and_scedule,
    get_continue_ids,
    delete_expired_data, extend_working_time,
    SCAN_TIME_DELTA, MIN_BEFORE_DELETE,
    get_active_infobases
)


me_id: str = ''
dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    if message.from_user:
        await message.answer(f'Hello {message.from_user.full_name}!')


@dp.message(Command('create_infobase'))
async def create_infobase(message: types.Message) -> None:
    ibase, sch = create_infobase_and_scedule()
    await message.answer('OK')


@dp.message(Command('list_active_infobases'))
async def list_active_infobases(message: types.Message) -> None:
    lst = get_active_infobases()
    msg = "\n".join(lst)
    await message.answer(msg)


@dp.message(Command("help"))
async def help_command(message: types.Message) -> None:
    await message.answer(
        """
**Справка**

Этот бот управляет конфигурацией 1С
может содавать их, а также отслеживать
состояние. В случае окончания периода
активности - отключать ее, предварительно
предупредив о действии.
        """
    )


@dp.callback_query(F.data.contains('continue_'))
async def send_random_value(callback: types.CallbackQuery):
    if callback.data:
        infobase_id = callback.data.split('_')[1]
        extend_working_time(infobase_id)
        if callback.message:
            await callback.message.answer(
                f'Время работы  {infobase_id} продлено'
            )
            await callback.answer()


async def main(bot: Bot) -> None:
    await dp.start_polling(bot)


async def send_message(bot: Bot, infobase_id=None, message=''):
    builder = InlineKeyboardBuilder()
    if infobase_id:
        builder.add(
            types.InlineKeyboardButton(
                text='Продлить? ',
                callback_data='continue_' + infobase_id
            )
        )
    await bot.send_message(
        me_id, message, reply_markup=builder.as_markup())


async def check_infobases(bot: Bot):
    """
    Checks infobase_dispatch table
    """
    dt = datetime.now()

    # удаляем просроченные данные
    amount = delete_expired_data(dt)
    if amount > 0:
        await send_message(bot=bot, message=f'Выключено {amount} инфобаз')

    # получаем данные готовые к продлению
    continue_ids = get_continue_ids(dt)

    # информируем пользователя о нихы
    for i in continue_ids:
        await send_message(
            bot=bot, infobase_id=i,
            message=f'У базы {i} осталось {MIN_BEFORE_DELETE} мин'
        )


if __name__ == '__main__':
    load_dotenv()
    # API чатбота
    API_TOKEN = getenv('API_TOKEN', '')
    # зесь помести id своего аккаунта
    me_id = getenv('MY_CHAT_ID', '')
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    create_db_and_tables()
    # создаем экземпляр бота
    bot = Bot(token=API_TOKEN)

    loop = asyncio.get_event_loop()

    # запускаем периодическую функцию проверки БД
    loop.create_task(
        periodic(
            SCAN_TIME_DELTA.seconds, check_infobases, bot
        )
    )

    # запускаем основную функцию бота
    loop.run_until_complete(main(bot))
