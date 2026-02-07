import json
import os
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query
import traceback
from db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from api.parser.persistence_service import PersistenceService 
from api.parser.parser_service import ParserService

parser_router = APIRouter()

@parser_router.post("/upload/", status_code=201)
async def upload_file_and_parse(
    file: UploadFile = File(...),
    # Параметры для справочника (опционально)
    reference_name: str = Query(None, description="Название справочника для загрузки конфигурации"),
    # Параметры для ручного ввода (опционально)
    chapters: str = Form(None, description="JSON строка или comma-separated строка"),
    cycles: str = Form(None, description="JSON строка или comma-separated строка"),
    modules: str = Form(None, description="JSON строка или comma-separated строка"),
    db_session: AsyncSession = Depends(get_db)
):
    file_path = None

    # Приоритет: справочник > ручной ввод > значения по умолчанию
    if reference_name:
        # Загрузка из справочника
        parser = ParserService()
        try:
            chapters_list, cycles_list, modules_list = parser.load_config_from_reference(reference_name)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        # Парсинг из формы (ручной ввод)
        try:
            chapters_list = json.loads(chapters) if chapters else ["ОП", "ПП"]
        except (json.JSONDecodeError, TypeError):
            chapters_list = [item.strip() for item in chapters.split(',') if item.strip()] if chapters else ["ОП", "ПП"]

        try:
            cycles_list = json.loads(cycles) if cycles else ["НО", "ОО", "СО", "ОГСЭ", "ЕН", "ОПЦ", "ПЦ"]
        except (json.JSONDecodeError, TypeError):
            cycles_list = [item.strip() for item in cycles.split(',') if item.strip()] if cycles else ["НО", "ОО", "СО", "ОГСЭ", "ЕН", "ОПЦ", "ПЦ"]

        try:
            modules_list = json.loads(modules) if modules else ["ОУД", "ПОО", "ПМ.02", "ПМ.03", "ПМ.05", "ПМ.06", "ПМ.07"]
        except (json.JSONDecodeError, TypeError):
            modules_list = [item.strip() for item in modules.split(',') if item.strip()] if modules else ["ОУД", "ПОО", "ПМ.02", "ПМ.03", "ПМ.05", "ПМ.06", "ПМ.07"]

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
            "message": "Файл успешно загружен, спарсен и данные сохранены в БД",
            "used_reference": reference_name  # Указываем, какой справочник использовался (если был)
        }

    except Exception as e:
        print(f"Ошибка при парсинге или сохранении в БД: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка при парсинге файла или сохранении в БД: {str(e)}")
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Временный файл {file.filename} удален.")
            except OSError as e:
                print(f"Не удалось удалить временный файл {file.filename}: {e}")


@parser_router.get("/references/")
async def get_available_references():
    """
    Возвращает список доступных справочников.
    """
    parser = ParserService()
    refs = parser.get_reference_lists()
    return {"references": list(refs.keys()), "configs": refs}


@parser_router.post("/references/create/", status_code=201)
async def create_reference(
    name: str = Form(..., description="Имя справочника"),
    chapters: str = Form(..., description="JSON строка или comma-separated строка"),
    cycles: str = Form(..., description="JSON строка или comma-separated строка"),
    modules: str = Form(..., description="JSON строка или comma-separated строка")
):
    """
    Создает новый справочник в JSON-файле.
    """
    # Парсим параметры
    try:
        chapters_list = json.loads(chapters)
    except json.JSONDecodeError:
        chapters_list = [item.strip() for item in chapters.split(',') if item.strip()]

    try:
        cycles_list = json.loads(cycles)
    except json.JSONDecodeError:
        cycles_list = [item.strip() for item in cycles.split(',') if item.strip()]

    try:
        modules_list = json.loads(modules)
    except json.JSONDecodeError:
        modules_list = [item.strip() for item in modules.split(',') if item.strip()]

    # Создаем экземпляр парсера и сохраняем справочник
    parser = ParserService()
    parser.save_reference_to_file(name, chapters_list, cycles_list, modules_list)

    return {
        "name": name,
        "chapters": chapters_list,
        "cycles": cycles_list,
        "modules": modules_list,
        "message": f"Справочник '{name}' успешно создан"
    }


@parser_router.delete("/references/{reference_name}/", status_code=200)
async def delete_reference(reference_name: str):
    """
    Удаляет справочник из JSON-файла.
    """
    parser = ParserService()
    refs = parser.get_reference_lists()
    
    if reference_name not in refs:
        raise HTTPException(status_code=404, detail=f"Справочник '{reference_name}' не найден")
    
    del refs[reference_name]
    
    # Перезаписываем файл
    with open(parser.reference_file_path, 'w', encoding='utf-8') as f:
        json.dump(refs, f, ensure_ascii=False, indent=2)
    
    return {"message": f"Справочник '{reference_name}' успешно удален"}


@parser_router.put("/references/{reference_name}/", status_code=200)
async def update_reference(
    reference_name: str,
    chapters: str = Form(..., description="JSON строка или comma-separated строка"),
    cycles: str = Form(..., description="JSON строка или comma-separated строка"),
    modules: str = Form(..., description="JSON строка или comma-separated строка")
):
    """
    Обновляет существующий справочник.
    """
    parser = ParserService()
    refs = parser.get_reference_lists()
    
    if reference_name not in refs:
        raise HTTPException(status_code=404, detail=f"Справочник '{reference_name}' не найден")
    
    # Парсим параметры
    try:
        chapters_list = json.loads(chapters)
    except json.JSONDecodeError:
        chapters_list = [item.strip() for item in chapters.split(',') if item.strip()]

    try:
        cycles_list = json.loads(cycles)
    except json.JSONDecodeError:
        cycles_list = [item.strip() for item in cycles.split(',') if item.strip()]

    try:
        modules_list = json.loads(modules)
    except json.JSONDecodeError:
        modules_list = [item.strip() for item in modules.split(',') if item.strip()]

    # Обновляем справочник
    refs[reference_name] = {
        "chapters": chapters_list,
        "cycles": cycles_list,
        "modules": modules_list
    }
    
    # Перезаписываем файл
    with open(parser.reference_file_path, 'w', encoding='utf-8') as f:
        json.dump(refs, f, ensure_ascii=False, indent=2)
    
    return {
        "name": reference_name,
        "chapters": chapters_list,
        "cycles": cycles_list,
        "modules": modules_list,
        "message": f"Справочник '{reference_name}' успешно обновлен"
    }