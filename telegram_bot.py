from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from BOT_TOKEN import TOKEN
import os
from pathlib import Path

from p2txt import process_pdf

raw_pdf_path = Path('pdf_raw')
processed_pdf_path = Path('pdf_processed')

# Создаем директории если их нет
raw_pdf_path.mkdir(exist_ok=True)
processed_pdf_path.mkdir(exist_ok=True)

bot = Bot(token=TOKEN)
dp = Dispatcher()

DOWNLOADS_DIR = "files"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Список для хранения информации о обработанных файлах
processed_files_info = []

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет, я бот рецензировщик! Отправь мне PDF файл статьи для рецензии")

@dp.message(F.text)
async def echo_message(message: types.Message):
    await message.answer(f"Ты написал: {message.text}, круто")

def process_single_pdf(pdf_path, original_name):
    """Обработка одного PDF файла"""
    try:
        # Сохраняем оригинальный файл в raw_pdf_path
        raw_file_path = raw_pdf_path / original_name
        # Копируем файл (если нужно сохранить оригинал)
        with open(pdf_path, 'rb') as src, open(raw_file_path, 'wb') as dst:
            dst.write(src.read())
        
        # Обрабатываем PDF и сохраняем результат в processed_pdf_path
        success = process_pdf(Path(pdf_path), processed_pdf_path)
        
        if success:
            # Ищем созданный txt файл
            txt_file_path = processed_pdf_path / f"{Path(original_name).stem}.txt"
            if txt_file_path.exists():
                return {
                    "success": True, 
                    "message": f"✅ Файл '{original_name}' успешно обработан!",
                    "txt_path": str(txt_file_path),
                    "original_name": original_name
                }
            else:
                return {"success": False, "message": f"❌ Ошибка: TXT файл не создан для '{original_name}'"}
        else:
            return {"success": False, "message": f"❌ Ошибка при обработке файла '{original_name}'"}
            
    except Exception as e:
        return {"success": False, "message": f"❌ Ошибка при обработке '{original_name}': {str(e)}"}

@dp.message(F.document)
async def handle_document(message: types.Message):
    file_id = message.document.file_id
    file_name = message.document.file_name
    
    if not file_name.lower().endswith('.pdf'):
        await message.answer("Файл должен быть в формате PDF :(")
        return
    
    await message.answer("Скачиваю файл...")
    file_path = os.path.join(DOWNLOADS_DIR, file_name)
    
    try:
        await bot.download(file_id, destination=file_path)
        await message.answer(f"Файл '{file_name}' успешно скачан!")
        
        # Обрабатываем PDF
        result = process_single_pdf(file_path, file_name)
        await message.answer(result["message"])
        
        # Сохраняем информацию о обработанном файле
        if result["success"]:
            processed_files_info.append({
                "original_name": result["original_name"],
                "txt_path": result["txt_path"],
                "timestamp": str(Path(result["txt_path"]).stat().st_mtime)
            })
            print(f"Добавлен в список: {result['original_name']}")
        
        # Если обработка успешна, отправляем текст из TXT файла
        if result["success"] and "txt_path" in result:
            try:
                with open(result["txt_path"], 'r', encoding='utf-8') as txt_file:
                    txt_content = txt_file.read()
                
                # # Отправляем текст из файла (обрезаем если слишком длинный)
                # if len(txt_content) > 4000:
                #     await message.answer(txt_content[:4000] + "\n\n... (текст обрезан)")
                # else:
                #     await message.answer(txt_content)
                
            except Exception as e:
                await message.answer(f"⚠️ Файл обработан, но возникла ошибка при чтении результата: {str(e)}")
        
    except Exception as e:
        await message.answer("❌ Ошибка при скачивании файла.")
        print(f"Ошибка: {e}")

# Команда для просмотра списка обработанных файлов
@dp.message(Command("files"))
async def show_processed_files(message: types.Message):
    """Показать список обработанных файлов"""
    if not processed_files_info:
        await message.answer("📝 Список обработанных файлов пуст")
        return
    
    response = f"📝 Обработанные файлы ({len(processed_files_info)}):\n\n"
    for i, file_info in enumerate(processed_files_info, 1):
        response += f"{i}. {file_info['original_name']}\n"
    
    await message.answer(response)

# Команда для очистки списка обработанных файлов
@dp.message(Command("clear_list"))
async def clear_processed_files_list(message: types.Message):
    """Очистить список обработанных файлов"""
    global processed_files_info
    processed_files_info.clear()
    await message.answer("🗑️ Список обработанных файлов очищен")

# Добавляем команду для очистки временных файлов
@dp.message(Command("clean"))
async def clean_files(message: types.Message):
    """Команда очистки временных файлов"""
    try:
        # Очищаем downloads директорию
        for file_path in Path(DOWNLOADS_DIR).glob("*"):
            file_path.unlink()
        
        await message.answer("🧹 Временные файлы очищены")
    except Exception as e:
        await message.answer(f"❌ Ошибка при очистке: {str(e)}")


async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
