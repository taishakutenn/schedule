from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import List
import json
import os
import traceback
from db.session import get_db

from sqlalchemy.ext.asyncio import AsyncSession
from api.parser.persistence_service import PersistenceService 
from api.parser.parser_service import ParserService

parser_router = APIRouter()

@parser_router.post("/upload/", status_code=201)
async def upload_file_and_parse(
    file: UploadFile = File(...),
    chapters: str = Form(...),
    cycles: str = Form(...),
    modules: str = Form(...),
    db_session: AsyncSession = Depends(get_db)
):
    file_path = None

    try:
        try:
            chapters_list = json.loads(chapters) if chapters else ["ОП", "ПП"]
        except json.JSONDecodeError:
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

    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, file.filename)
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    print(f"Загружен файл: {file.filename}")
    print(f"Список разделов: {chapters_list}")
    print(f"Список циклов: {cycles_list}")
    print(f"Список модулей: {modules_list}")

    try:
        parser = ParserService(
            chapters=chapters_list,
            cycles=cycles_list,
            modules=modules_list,
            sheet_name="План"
        )

        result = parser.parse_excel_file(file_path)
        # print("DEBUG: Result from parser (raw):", result)
        # print("DEBUG: Type of result (raw):", type(result)) 

        persistence_service = PersistenceService(db_session)

        async with db_session.begin():
            saved_plan_id = await persistence_service.save_parsed_data(result)

        return {
            "filename": file.filename,
            "size": len(contents),
            "chapters_count": len(chapters_list),
            "cycles_count": len(cycles_list),
            "modules_count": len(modules_list),
            "parsed_data": result,
            "saved_plan_id": saved_plan_id, 
            "message": "Файл успешно загружен, спарсен и данные сохранены в БД"
        }

    except Exception as e:
        print(f"Ошибка при парсинге или сохранении в БД: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка при парсинге файла или сохранении в БД: {str(e)}")
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Временный файл {file_path} удален.")
            except OSError as e:
                print(f"Не удалось удалить временный файл {file_path}: {e}")
