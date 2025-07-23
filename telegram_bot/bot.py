from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from BOT_TOKEN import TOKEN
import os

bot = Bot(token=TOKEN)
dp = Dispatcher()

DOWNLOADS_DIR = "files"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет, я бот рецензировщик, отправь мне pdf файл статьи для рецензии")

@dp.message(F.text)
async def echo_message(message: types.Message):
    await message.answer(f"Ты написал: {message.text}, круто")

def do_smth_with_pdf(path):
    '''
    PLACEHOLDER FOR LLM
    '''
    try:
        return f'Файл весит {os.path.getsize(path) / (1024 ** 2):.2} мб'
    except Exception as e:
        return {"error": str(e)}

@dp.message(F.document)
async def handle_document(message: types.Message):
    file_id = message.document.file_id
    file_name = message.document.file_name
    if file_name.split('.')[-1] != 'pdf':
        await message.answer("файл должен быть pdf формата :(")
    else:
        await message.answer("Скачиваю файл...")
        file_path = os.path.join(DOWNLOADS_DIR, file_name)
        try:
            await bot.download(file_id, destination=file_path)
            await message.answer(f"Файл '{file_name}' успешно сохранён!")
            await message.answer(f'{do_smth_with_pdf(file_path)}')
        except Exception as e:
            await message.answer("Ошибка при скачивании файла.")
            print(f"Ошибка: {e}")


async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
