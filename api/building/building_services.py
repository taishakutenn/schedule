from api.building.building_pydantic import *
from api.services_helpers import ensure_building_exists, ensure_building_unique 
from api.building.building_DAL import BuildingDAL
from fastapi import HTTPException, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class BuildingService:
    async def _create_new_building(self, body: CreateBuilding, request: Request, db) -> ShowBuildingWithHATEOAS:
        async with db as session:
            async with session.begin():
                building_dal = BuildingDAL(session)
                try:
                    if not await ensure_building_unique(building_dal, body.building_number):
                        raise HTTPException(status_code=400, detail=f"Здание с номером {body.building_number} уже существует")

                    building = await building_dal.create_building(
                        building_number=body.building_number,
                        city=body.city,
                        building_address=body.building_address
                    )
                    building_number = building.building_number
                    building_pydantic = ShowBuilding.model_validate(building, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
                        "update": f'{api_base_url}/buildings/update',
                        "delete": f'{api_base_url}/buildings/delete/{building_number}',
                        "buildings": f'{api_base_url}/buildings',
                        "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
                    }

                    return ShowBuildingWithHATEOAS(building=building_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при создании здания: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_building_by_number(self, building_number, request: Request, db) -> ShowBuildingWithHATEOAS:
        async with db as session:
            async with session.begin():
                building_dal = BuildingDAL(session)
                try:
                    building = await building_dal.get_building_by_number(building_number)
                    if not building:
                        raise HTTPException(status_code=404, detail=f"Здание с номером: {building_number} не найдено")
                    building_pydantic = ShowBuilding.model_validate(building, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
                        "update": f'{api_base_url}/buildings/update',
                        "delete": f'{api_base_url}/buildings/delete/{building_number}',
                        "buildings": f'{api_base_url}/buildings',
                        "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
                    }

                    return ShowBuildingWithHATEOAS(building=building_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение здания отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_building_by_address(self, address, request: Request, db) -> ShowBuildingWithHATEOAS:
        async with db as session:
            async with session.begin():
                building_dal = BuildingDAL(session)
                try:
                    building = await building_dal.get_building_by_address(address)
                    if not building:
                        raise HTTPException(status_code=404, detail=f"Здание по адресу: {address} не найдено")
                    building_number = building.building_number
                    building_pydantic = ShowBuilding.model_validate(building, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
                        "update": f'{api_base_url}/buildings/update',
                        "delete": f'{api_base_url}/buildings/delete/{building_number}',
                        "buildings": f'{api_base_url}/buildings',
                        "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
                    }

                    return ShowBuildingWithHATEOAS(building=building_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение здания отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_all_buildings(self, page: int, limit: int, request: Request, db) -> ShowBuildingListWithHATEOAS:
        async with db as session:
            async with session.begin():
                building_dal = BuildingDAL(session)
                try:
                    buildings = await building_dal.get_all_buildings(page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    buildings_with_hateoas = []
                    for building in buildings:
                        building_pydantic = ShowBuilding.model_validate(building, from_attributes=True)
                        building_number = building.building_number
                        building_links = {
                            "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
                            "update": f'{api_base_url}/buildings/update',
                            "delete": f'{api_base_url}/buildings/delete/{building_number}',
                            "buildings": f'{api_base_url}/buildings',
                            "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
                        }
                        building_with_links = ShowBuildingWithHATEOAS(building=building_pydantic, links=building_links)
                        buildings_with_hateoas.append(building_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/buildings/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/buildings/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowBuildingListWithHATEOAS(buildings=buildings_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение зданий отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _delete_building(self, building_number: int, request: Request, db) -> ShowBuildingWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    building_dal = BuildingDAL(session)
                    if not await ensure_building_exists(building_dal, building_number):
                        raise HTTPException(status_code=404, detail=f"Здание с номером: {building_number} не найдено")

                    building = await building_dal.delete_building(building_number)
                    if not building:
                        raise HTTPException(status_code=404, detail=f"Здание с номером: {building_number} не найдено")

                    building_pydantic = ShowBuilding.model_validate(building, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "buildings": f'{api_base_url}/buildings',
                        "create": f'{api_base_url}/buildings/create',
                        "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowBuildingWithHATEOAS(building=building_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при удалении здания {building_number}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении здания.")


    async def _update_building(self, body: UpdateBuilding, request: Request, db) -> ShowBuildingWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["building_number", "new_building_number"]}
                    if body.new_building_number is not None:
                        update_data["building_number"] = body.new_building_number
                        building_dal = BuildingDAL(session)
                        if not await ensure_building_unique(building_dal, body.new_building_number):
                            raise HTTPException(status_code=400, detail=f"Здание с номером {body.new_building_number} уже существует")

                    building_dal = BuildingDAL(session)
                    if not await ensure_building_exists(building_dal, body.building_number):
                        raise HTTPException(status_code=404, detail=f"Здание с номером: {body.building_number} не найдено")

                    building = await building_dal.update_building(target_number=body.building_number, **update_data)
                    if not building:
                        raise HTTPException(status_code=404, detail=f"Здание с номером: {body.building_number} не найдено")

                    building_number = building.building_number 
                    building_pydantic = ShowBuilding.model_validate(building, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/buildings/search/by_number/{building_number}',
                        "update": f'{api_base_url}/buildings/update',
                        "delete": f'{api_base_url}/buildings/delete/{building_number}',
                        "buildings": f'{api_base_url}/buildings',
                        "cabinets": f'{api_base_url}/cabinets/search/by_building/{building_number}'
                    }

                    return ShowBuildingWithHATEOAS(building=building_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.warning(f"Изменение данных о здании отменено (Ошибка: {e})")
                raise e