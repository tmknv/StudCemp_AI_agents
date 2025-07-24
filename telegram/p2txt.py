import fitz  # PyMuPDF
import re
import time
from pathlib import Path
from datetime import datetime

def clean_text(text):
    """Очистка извлеченного текста"""
    # Удаляем лишние пробелы и переносы строк
    text = re.sub(r'\s+', ' ', text).strip()
    # Удаляем специальные символы, сохраняя пунктуацию
    text = re.sub(r'[^\w\s.,:;!?()\-—–\'\"\n]', '', text)
    # Восстанавливаем нормальные абзацы
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text

def process_pdf(pdf_path, output_folder, clean=True):
    """Обрабатывает один PDF-файл с помощью PyMuPDF"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        for page in doc:
            text += page.get_text() + "\n\n"
        
        if not text.strip():
            print(f"Не удалось извлечь текст из {pdf_path.name}")
            return False
        
        if clean:
            text = clean_text(text)
        
        # Создаем папку для результатов
        output_folder.mkdir(exist_ok=True)
        
        # Сохраняем в файл
        output_path = output_folder / f"{pdf_path.stem}.txt"
        output_path.write_text(text, encoding='utf-8')
        
        print(f"✅ {pdf_path.name} → {output_path.name} ({len(doc)} стр.)")
        return True
        
    except Exception as e:
        print(f" Ошибка при обработке {pdf_path.name}: {str(e)}")
        return False

def batch_process_pdfs(input_folder=None, output_folder_name="extracted_texts"):
    """Пакетная обработка всех PDF в папке"""
    # Определяем рабочую папку
    input_folder = Path(input_folder) if input_folder else Path.cwd()
    
    print(f"\n Обрабатываю PDF-файлы в папке: {input_folder}")
    
    # Находим все PDF-файлы
    pdf_files = list(input_folder.glob("*.pdf"))
    if not pdf_files:
        print(" PDF-файлы не найдены!")
        return
    
    # Создаем папку для результатов
    output_folder = input_folder / output_folder_name
    output_folder.mkdir(exist_ok=True)
    
    print(f" Найдено PDF-файлов: {len(pdf_files)}")
    print(" Начинаю обработку...\n")
    
    start_time = time.time()
    success_count = 0
    
    # Обрабатываем каждый файл
    for pdf_file in pdf_files:
        if process_pdf(pdf_file, output_folder):
            success_count += 1
    
    # Формируем отчет
    total_time = time.time() - start_time
    print(f"\n{'='*40}")
    print(f" Обработка завершена!")
    print(f" Успешно: {success_count}/{len(pdf_files)}")
    print(f" Время: {total_time:.2f} сек")
    print(f" Результаты в: {output_folder}")
    print(f"{'='*40}")

if __name__ == "__main__":
    # Автоматический запуск обработки
    batch_process_pdfs()
