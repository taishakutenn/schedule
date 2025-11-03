from api.speciality.speciality_pydantic import *
from api.services_helpers import ensure_speciality_exists, ensure_speciality_unique 
from api.speciality.speciality_DAL import SpecialityDAL
from fastapi import HTTPException, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class SpecialityService:
    async def _create_new_speciality(self, body: CreateSpeciality, request: Request, db) -> ShowSpecialityWithHATEOAS:
        async with db as session:
            async with session.begin():
                speciality_dal = SpecialityDAL(session)
                try:
                    if not await ensure_speciality_unique(speciality_dal, body.speciality_code):
                        raise HTTPException(status_code=400, detail=f"Специальность с кодом '{body.speciality_code}' уже существует")

                    speciality = await speciality_dal.create_speciality(
                        speciality_code=body.speciality_code
                    )
                    speciality_code = speciality.speciality_code
                    speciality_pydantic = ShowSpeciality.model_validate(speciality, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/specialities/search/by_speciality_code/{speciality_code}',
                        "update": f'{api_base_url}/specialities/update',
                        "delete": f'{api_base_url}/specialities/delete/{speciality_code}',
                        "specialities": f'{api_base_url}/specialities',
                        "groups": f'{api_base_url}/groups/search/by_speciality/{speciality_code}',
                        "plans": f'{api_base_url}/plans/search/by_speciality/{speciality_code}'
                    }

                    return ShowSpecialityWithHATEOAS(speciality=speciality_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при создании специальности '{body.speciality_code}': {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_speciality_by_code(self, speciality_code: str, request: Request, db) -> ShowSpecialityWithHATEOAS:
        async with db as session:
            async with session.begin():
                speciality_dal = SpecialityDAL(session)
                try:
                    speciality = await speciality_dal.get_speciality(speciality_code)
                    if not speciality:
                        raise HTTPException(status_code=404, detail=f"Специальность с кодом '{speciality_code}' не найдена")
                    speciality_pydantic = ShowSpeciality.model_validate(speciality, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/specialities/search/by_speciality_code/{speciality_code}',
                        "update": f'{api_base_url}/specialities/update',
                        "delete": f'{api_base_url}/specialities/delete/{speciality_code}',
                        "specialities": f'{api_base_url}/specialities',
                        "groups": f'{api_base_url}/groups/search/by_speciality/{speciality_code}',
                        "plans": f'{api_base_url}/plans/search/by_speciality/{speciality_code}'
                    }

                    return ShowSpecialityWithHATEOAS(speciality=speciality_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение специальности '{speciality_code}' отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_all_specialities(self, page: int, limit: int, request: Request, db) -> ShowSpecialityListWithHATEOAS:
        async with db as session:
            async with session.begin():
                speciality_dal = SpecialityDAL(session)
                try:
                    specialities = await speciality_dal.get_all_specialities(page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    specialities_with_hateoas = []
                    for speciality in specialities:
                        speciality_pydantic = ShowSpeciality.model_validate(speciality, from_attributes=True)
                        speciality_code = speciality.speciality_code
                        speciality_links = {
                            "self": f'{api_base_url}/specialities/search/by_speciality_code/{speciality_code}',
                            "update": f'{api_base_url}/specialities/update',
                            "delete": f'{api_base_url}/specialities/delete/{speciality_code}',
                            "specialities": f'{api_base_url}/specialities',
                            "groups": f'{api_base_url}/groups/search/by_speciality/{speciality_code}',
                            "plans": f'{api_base_url}/plans/search/by_speciality/{speciality_code}'
                        }
                        speciality_with_links = ShowSpecialityWithHATEOAS(speciality=speciality_pydantic, links=speciality_links)
                        specialities_with_hateoas.append(speciality_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/specialities/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/specialities/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowSpecialityListWithHATEOAS(specialities=specialities_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение специальностей отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _delete_speciality(self, speciality_code: str, request: Request, db) -> ShowSpecialityWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    speciality_dal = SpecialityDAL(session)
                    
                    if not await ensure_speciality_exists(speciality_dal, speciality_code):
                        raise HTTPException(status_code=404, detail=f"Специальность с кодом '{speciality_code}' не найдена")

                    speciality = await speciality_dal.delete_speciality(speciality_code)
                    
                    if not speciality:
                        raise HTTPException(status_code=404, detail=f"Специальность с кодом '{speciality_code}' не найдена")

                    speciality_pydantic = ShowSpeciality.model_validate(speciality, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "specialities": f'{api_base_url}/specialities',
                        "create": f'{api_base_url}/specialities/create'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowSpecialityWithHATEOAS(speciality=speciality_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при удалении специальности '{speciality_code}': {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении специальности.")


    async def _update_speciality(self, body: UpdateSpeciality, request: Request, db) -> ShowSpecialityWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["speciality_code", "new_speciality_code"]}
                    
                    if body.new_speciality_code is not None:
                        update_data["speciality_code"] = body.new_speciality_code
                        
                        speciality_dal = SpecialityDAL(session)
                        if not await ensure_speciality_unique(speciality_dal, body.new_speciality_code):
                            raise HTTPException(status_code=400, detail=f"Специальность с кодом '{body.new_speciality_code}' уже существует")

                    speciality_dal = SpecialityDAL(session)
                    
                    if not await ensure_speciality_exists(speciality_dal, body.speciality_code):
                        raise HTTPException(status_code=404, detail=f"Специальность с кодом '{body.speciality_code}' не найдена")

                    speciality = await speciality_dal.update_speciality(target_code=body.speciality_code, **update_data)
                    if not speciality:
                        raise HTTPException(status_code=404, detail=f"Специальность с кодом '{body.speciality_code}' не найдена")

                    speciality_code = speciality.speciality_code 
                    speciality_pydantic = ShowSpeciality.model_validate(speciality, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/specialities/search/by_speciality_code/{speciality_code}',
                        "update": f'{api_base_url}/specialities/update',
                        "delete": f'{api_base_url}/specialities/delete/{speciality_code}',
                        "specialities": f'{api_base_url}/specialities',
                        "groups": f'{api_base_url}/groups/search/by_speciality/{speciality_code}',
                        "plans": f'{api_base_url}/plans/search/by_speciality/{speciality_code}'
                    }

                    return ShowSpecialityWithHATEOAS(speciality=speciality_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.warning(f"Изменение данных о специальности отменено (Ошибка: {e})")
                raise e
            