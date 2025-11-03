from api.cabinet.cabinet_pydantic import *
from api.services_helpers import ensure_cabinet_exists, ensure_cabinet_unique, ensure_building_exists
from api.cabinet.cabinet_DAL import CabinetDAL
from api.building.building_DAL import BuildingDAL
from fastapi import HTTPException, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class CabinetService:
    async def _create_new_cabinet(self, body: CreateCabinet, request: Request, db) -> ShowCabinetWithHATEOAS:
        async with db as session:
            async with session.begin():
                building_dal = BuildingDAL(session)
                cabinet_dal = CabinetDAL(session)
                try:
                    # Check that the building exists
                    if not await ensure_building_exists(building_dal, body.building_number):
                        raise HTTPException(status_code=404,
                                            detail=f"Здание с номером {body.building_number} не найдено")
                    # Check that the cabinet is unique
                    if not await ensure_cabinet_unique(cabinet_dal, body.building_number, body.cabinet_number):
                        raise HTTPException(status_code=400,
                                            detail=f"Кабинет с номером {body.cabinet_number} в здании {body.building_number} уже существует")

                    cabinet = await cabinet_dal.create_cabinet(
                        cabinet_number=body.cabinet_number,
                        building_number=body.building_number,
                        capacity=body.capacity,
                        cabinet_state=body.cabinet_state
                    )
                    cabinet_number = cabinet.cabinet_number
                    building_number = cabinet.building_number
                    cabinet_pydantic = ShowCabinet.model_validate(cabinet, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
                        "update": f'{api_base_url}/cabinets/update',
                        "delete": f'{api_base_url}/cabinets/delete/{building_number}/{cabinet_number}',
                        "cabinets": f'{api_base_url}/cabinets',
                        "building": f'{api_base_url}/buildings/search/by_number/{building_number}',
                        "sessions": f'{api_base_url}/sessions/search/by_cabinet/{building_number}/{cabinet_number}'
                    }

                    return ShowCabinetWithHATEOAS(cabinet=cabinet_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при создании кабинета: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_cabinet_by_number_and_building(self, building_number: int, cabinet_number: int, request: Request, db) -> ShowCabinetWithHATEOAS:
        async with db as session:
            async with session.begin():
                cabinet_dal = CabinetDAL(session)
                try:
                    cabinet = await cabinet_dal.get_cabinet_by_number_and_building(building_number, cabinet_number)
                    if not cabinet:
                        raise HTTPException(status_code=404, detail=f"Кабинет с номером {cabinet_number} в здании {building_number} не найден")
                    cabinet_pydantic = ShowCabinet.model_validate(cabinet, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
                        "update": f'{api_base_url}/cabinets/update',
                        "delete": f'{api_base_url}/cabinets/delete/{building_number}/{cabinet_number}',
                        "cabinets": f'{api_base_url}/cabinets',
                        "building": f'{api_base_url}/buildings/search/by_number/{building_number}',
                        "sessions": f'{api_base_url}/sessions/search/by_cabinet/{building_number}/{cabinet_number}'
                    }

                    return ShowCabinetWithHATEOAS(cabinet=cabinet_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение кабинета отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_all_cabinets(self, page: int, limit: int, request: Request, db) -> ShowCabinetListWithHATEOAS:
        async with db as session:
            async with session.begin():
                cabinet_dal = CabinetDAL(session)
                try:
                    cabinets = await cabinet_dal.get_all_cabinets(page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    cabinets_with_hateoas = []
                    for cabinet in cabinets:
                        cabinet_pydantic = ShowCabinet.model_validate(cabinet, from_attributes=True)
                        cabinet_number = cabinet.cabinet_number
                        building_number = cabinet.building_number
                        cabinet_links = {
                            "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
                            "update": f'{api_base_url}/cabinets/update',
                            "delete": f'{api_base_url}/cabinets/delete/{building_number}/{cabinet_number}',
                            "cabinets": f'{api_base_url}/cabinets',
                            "building": f'{api_base_url}/buildings/search/by_number/{building_number}',
                            "sessions": f'{api_base_url}/sessions/search/by_cabinet/{building_number}/{cabinet_number}'
                        }
                        cabinet_with_links = ShowCabinetWithHATEOAS(cabinet=cabinet_pydantic, links=cabinet_links)
                        cabinets_with_hateoas.append(cabinet_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/cabinets/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/cabinets/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowCabinetListWithHATEOAS(cabinets=cabinets_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение кабинетов отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_cabinets_by_building(self, building_number: int, page: int, limit: int, request: Request, db) -> ShowCabinetListWithHATEOAS:
        async with db as session:
            async with session.begin():
                building_dal = BuildingDAL(session)
                cabinet_dal = CabinetDAL(session)
                try:
                    # Check that the building exists
                    if not await ensure_building_exists(building_dal, building_number):
                        raise HTTPException(status_code=404,
                                            detail=f"Здание с номером {building_number} не найдено")

                    cabinets = await cabinet_dal.get_cabinets_by_building(building_number, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    cabinets_with_hateoas = []
                    for cabinet in cabinets:
                        cabinet_pydantic = ShowCabinet.model_validate(cabinet, from_attributes=True)
                        cabinet_number = cabinet.cabinet_number
                        cabinet_links = {
                            "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
                            "update": f'{api_base_url}/cabinets/update',
                            "delete": f'{api_base_url}/cabinets/delete/{building_number}/{cabinet_number}',
                            "cabinets": f'{api_base_url}/cabinets',
                            "building": f'{api_base_url}/buildings/search/by_number/{building_number}',
                            "sessions": f'{api_base_url}/sessions/search/by_cabinet/{building_number}/{cabinet_number}'
                        }
                        cabinet_with_links = ShowCabinetWithHATEOAS(cabinet=cabinet_pydantic, links=cabinet_links)
                        cabinets_with_hateoas.append(cabinet_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/cabinets/search/by_building/{building_number}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/cabinets/create',
                        "building": f'{api_base_url}/buildings/search/by_number/{building_number}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowCabinetListWithHATEOAS(cabinets=cabinets_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение кабинетов отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _delete_cabinet(self, building_number: int, cabinet_number: int, request: Request, db) -> ShowCabinetWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    cabinet_dal = CabinetDAL(session)
                    cabinet = await cabinet_dal.delete_cabinet(building_number, cabinet_number)
                    if not cabinet:
                        raise HTTPException(status_code=404, detail=f"Кабинет с номером: {cabinet_number} в здании {building_number} не может быть удалён, т.к. не найден")

                    cabinet_pydantic = ShowCabinet.model_validate(cabinet, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "cabinets": f'{api_base_url}/cabinets',
                        "create": f'{api_base_url}/cabinets/create',
                        "building": f'{api_base_url}/buildings/search/by_number/{building_number}'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowCabinetWithHATEOAS(cabinet=cabinet_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при удалении кабинета {cabinet_number} в здании {building_number}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении кабинета.")


    async def _update_cabinet(self, body: UpdateCabinet, request: Request, db) -> ShowCabinetWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    # exclusion of None-fields from the transmitted data
                    update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["building_number", "cabinet_number"]}
                    # Rename fields new_building_number and new_cabinet_number to building_number and cabinet_number
                    if "new_building_number" in update_data:
                        update_data["building_number"] = update_data.pop("new_building_number")
                    if "new_cabinet_number" in update_data:
                        update_data["cabinet_number"] = update_data.pop("new_cabinet_number")

                    # change data
                    cabinet_dal = CabinetDAL(session)
                    building_dal = BuildingDAL(session)

                    if not await ensure_cabinet_exists(cabinet_dal, body.building_number, body.cabinet_number):
                        raise HTTPException(status_code=404, detail=f"Кабинет с номером: {body.cabinet_number} в здании: {body.building_number} не найден")

                    target_building_number = body.building_number
                    target_cabinet_number = body.cabinet_number
                    if "building_number" in update_data or "cabinet_number" in update_data:
                        new_building_number = update_data.get("building_number", target_building_number)
                        new_cabinet_number = update_data.get("cabinet_number", target_cabinet_number)

                        if not await ensure_cabinet_unique(cabinet_dal, new_building_number, new_cabinet_number):
                            raise HTTPException(status_code=400, detail=f"Кабинет с номером {new_cabinet_number} в здании {new_building_number} уже существует")
                        if "building_number" in update_data and not await ensure_building_exists(building_dal, new_building_number):
                            raise HTTPException(status_code=404, detail=f"Здание с номером {new_building_number} не найдено")

                    cabinet = await cabinet_dal.update_cabinet(
                        search_building_number=body.building_number,
                        search_cabinet_number=body.cabinet_number,
                        **update_data
                    )
                    if not cabinet:
                        raise HTTPException(status_code=404, detail="Кабинет не был обновлён")

                    cabinet_number = cabinet.cabinet_number
                    building_number = cabinet.building_number
                    cabinet_pydantic = ShowCabinet.model_validate(cabinet, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}',
                        "update": f'{api_base_url}/cabinets/update',
                        "delete": f'{api_base_url}/cabinets/delete/{building_number}/{cabinet_number}',
                        "cabinets": f'{api_base_url}/cabinets',
                        "building": f'{api_base_url}/buildings/search/by_number/{building_number}',
                        "sessions": f'{api_base_url}/sessions/search/by_cabinet/{building_number}/{cabinet_number}'
                    }

                    return ShowCabinetWithHATEOAS(cabinet=cabinet_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.warning(f"Изменение данных о кабинете отменено (Ошибка: {e})")
                raise e