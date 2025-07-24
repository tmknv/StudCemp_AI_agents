from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from BOT_TOKEN import TOKEN
import os
import asyncio
import aiofiles
from pathlib import Path
import logging
from collections import deque

from p2txt import process_pdf
from AI_agents import get_result

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()

DOWNLOADS_DIR = "files"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Глобальная очередь обработки
processing_queue = deque()
is_processing = False

async def process_next_in_queue():
    global is_processing
    
    if is_processing or not processing_queue:
        return
    
    is_processing = True
    
    while processing_queue:
        # Берем следующего пользователя из очереди
        user_data = processing_queue.popleft()
        message = user_data['message']
        user_id = user_data['user_id']
        
        try:
            await process_user_file(message, user_data['file_id'], user_data['file_name'])
        except Exception as e:
            logger.error(f"Ошибка обработки для пользователя {user_id}: {e}")
            try:
                await message.answer(f"❌ Ошибка: {str(e)}")
            except:
                pass
        
        # Небольшая пауза между обработками
        await asyncio.sleep(1/3)
    
    is_processing = False

async def process_user_file(message: types.Message, file_id: str, file_name: str):
    await message.answer("📥 Скачиваю файл...")
    file_path = os.path.join(DOWNLOADS_DIR, file_name)
    
    # Скачиваем файл
    await bot.download(file_id, destination=file_path)
    await message.answer("✅ Файл скачан! Обрабатываю...")
    
    # Конвертируем PDF в текст
    processed_path = Path("temp_processed")
    processed_path.mkdir(exist_ok=True)
    
    # Обработка PDF
    loop = asyncio.get_event_loop()
    success = await loop.run_in_executor(None, process_pdf, Path(file_path), processed_path)
    
    if success:
        # Читаем текст статьи
        txt_file_path = processed_path / f"{Path(file_name).stem}.txt"
        if txt_file_path.exists():
            async with aiofiles.open(txt_file_path, 'r', encoding='utf-8') as txt_file:
                article_text = await txt_file.read()
            
            await message.answer("🧠 Генерирую обзор... Это может занять пару минут")
            
            # Генерируем обзор
            try:
                review_text = await loop.run_in_executor(None, get_result, article_text)
                
                # Отправляем обзор
                if len(review_text) > 4000:
                    parts = [review_text[i:i+4000] for i in range(0, len(review_text), 4000)]
                    for i, part in enumerate(parts, 1):
                        await message.answer(f"📄 Часть {i}/{len(parts)}:\n\n{part}")
                else:
                    await message.answer(f"📄 Обзор статьи:\n\n{review_text}")
                    
            except Exception as e:
                logger.error(f"Ошибка при генерации обзора: {e}")
                await message.answer(f"❌ Ошибка при генерации обзора: {str(e)}")
        else:
            await message.answer("❌ Ошибка: не удалось создать текстовый файл")
    else:
        await message.answer("❌ Ошибка при обработке PDF файла")
        
    # Удаляем все временные файлы
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        processed_path = Path("temp_processed")
        if processed_path.exists():
            for temp_file in processed_path.glob("*"):
                if temp_file.exists():
                    temp_file.unlink()
    except Exception as e:
        logger.error(f"Ошибка удаления временных файлов: {e}")

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет, я бот рецензировщик! Отправь мне PDF файл статьи для рецензии")

@dp.message(F.document)
async def handle_document(message: types.Message):
    global is_processing
    
    file_name = message.document.file_name
    
    if not file_name.lower().endswith('.pdf'):
        await message.answer("Файл должен быть в формате PDF :(")
        return
    
    # Добавляем пользователя в очередь
    processing_queue.append({
        'message': message,
        'user_id': message.from_user.id,
        'file_id': message.document.file_id,
        'file_name': file_name
    })
    
    position = len(processing_queue)
    if is_processing:
        await message.answer(f"⏳ Вы в очереди. Позиция: {position}")
    
    # Запускаем обработку очереди
    asyncio.create_task(process_next_in_queue())

async def main():
    logger.info("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
