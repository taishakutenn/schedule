from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List
import json
import os

from api.parser.parser_service import ParserService

parser_router = APIRouter()

@parser_router.post("/upload/", status_code=201)
async def upload_file_and_parse(
    file: UploadFile = File(...),
    chapters: str = Form(...), 
    cycles: str = Form(...),    
    modules: str = Form(...)    
):
    """
    Загружает файл и списки данных (разделы, циклы, модули), затем парсит файл.
    """
    try:
        # Преобразуем полученные строки в списки
        # Предполагаем, что строки передаются как "ОП,ПП" или ["ОП", "ПП"]
        
        # Пытаемся сначала как JSON
        try:
            chapters_list = json.loads(chapters) if chapters else ["ОП", "ПП"]
        except json.JSONDecodeError:
            # Если не JSON, то разбиваем по запятым
            chapters_list = [item.strip() for item in chapters.split(',') if item.strip()] if chapters else ["ОП", "ПП"]
        
        try:
            cycles_list = json.loads(cycles) if cycles else ["НО", "ОО", "СО", "ОГСЭ", "ЕН", "ОПЦ", "ПЦ"]
        except json.JSONDecodeError:
            cycles_list = [item.strip() for item in cycles.split(',') if item.strip()] if cycles else ["НО", "ОО", "СО", "ОГСЭ", "ЕН", "ОПЦ", "ПЦ"]
        
        try:
            modules_list = json.loads(modules) if modules else ["ОУД", "ПОО", "ПМ.02", "ПМ.03", "ПМ.05", "ПМ.06", "ПМ.07"]
        except json.JSONDecodeError:
            modules_list = [item.strip() for item in modules.split(',') if item.strip()] if modules else ["ОУД", "ПОО", "ПМ.02", "ПМ.03", "ПМ.05", "ПМ.06", "ПМ.07"]
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Неверный формат данных: {e}")

    # Создаём директорию для загрузок, если её нет
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    # Сохраняем загруженный файл
    file_path = os.path.join(upload_dir, file.filename)
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    print(f"Загружен файл: {file.filename}")
    print(f"Список разделов: {chapters_list}")
    print(f"Список циклов: {cycles_list}")
    print(f"Список модулей: {modules_list}")

    try:
        # Создаём экземпляр парсера
        parser = ParserService()
        
        # Устанавливаем переданные параметры
        parser.chapters = chapters_list
        parser.cycles = cycles_list
        parser.modules = modules_list
        
        # Парсим файл
        result = parser.parse_excel_file(file_path)
        
        # Удаляем временный файл после парсинга (опционально)
        # os.remove(file_path)
        
        return {
            "filename": file.filename,
            "size": len(contents),
            "chapters_count": len(chapters_list),
            "cycles_count": len(cycles_list),
            "modules_count": len(modules_list),
            "parsed_data": result,
            "message": "Файл успешно загружен и спарсен"
        }
        
    except Exception as e:
        # Удаляем временный файл в случае ошибки
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Ошибка при парсинге файла: {str(e)}")