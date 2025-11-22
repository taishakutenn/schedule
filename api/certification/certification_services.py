from api.certification.certification_pydantic import *
from api.services_helpers import ensure_certification_exists, ensure_subject_in_cycle_hours_exists
from api.certification.certification_DAL import CertificationDAL
from api.subject_in_cycle_hours.subject_in_cycle_hours_DAL import SubjectsInCycleHoursDAL
from fastapi import HTTPException, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class CertificationService:
    async def _create_new_certification(self, body: CreateCertification, request: Request, db) -> ShowCertificationWithHATEOAS:
        async with db as session:
            async with session.begin():
                subject_in_cycle_hours_dal = SubjectsInCycleHoursDAL(session)
                certification_dal = CertificationDAL(session)
                try:
                    if not await ensure_subject_in_cycle_hours_exists(subject_in_cycle_hours_dal, body.id):
                        raise HTTPException(status_code=404, detail=f"Запись о часах для предмета в цикле с id {body.id} не найдена")

                    certification = await certification_dal.create_certification(
                        id=body.id,
                        credit=body.credit,
                        differentiated_credit=body.differentiated_credit,
                        course_project=body.course_project,
                        course_work=body.course_work,
                        control_work=body.control_work,
                        other_form=body.other_form
                    )
                    certification_id = certification.id
                    certification_pydantic = ShowCertification.model_validate(certification, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/certifications/search/by_id/{certification_id}',
                        "update": f'{api_base_url}/certifications/update',
                        "delete": f'{api_base_url}/certifications/delete/{certification_id}',
                        "certifications": f'{api_base_url}/certifications',
                        "subjects_in_cycle_hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{certification_id}'
                    }

                    return ShowCertificationWithHATEOAS(certification=certification_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при создании сертификации для id {body.id}: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_certification_by_id(self, certification_id: int, request: Request, db) -> ShowCertificationWithHATEOAS:
        async with db as session:
            async with session.begin():
                certification_dal = CertificationDAL(session)
                try:
                    certification = await certification_dal.get_certification_by_id(certification_id)
                    if not certification:
                        raise HTTPException(status_code=404, detail=f"Сертификация с id {certification_id} не найдена")
                    certification_pydantic = ShowCertification.model_validate(certification, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/certifications/search/by_id/{certification_id}',
                        "update": f'{api_base_url}/certifications/update',
                        "delete": f'{api_base_url}/certifications/delete/{certification_id}',
                        "certifications": f'{api_base_url}/certifications',
                        "subjects_in_cycle_hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{certification_id}'
                    }

                    return ShowCertificationWithHATEOAS(certification=certification_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение сертификации {certification_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_all_certifications(self, page: int, limit: int, request: Request, db) -> ShowCertificationListWithHATEOAS:
        async with db as session:
            async with session.begin():
                certification_dal = CertificationDAL(session)
                try:
                    certifications = await certification_dal.get_all_certifications(page, limit)
                    if certifications is None:
                        certifications = []

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    certifications_with_hateoas = []
                    for certification in certifications:
                        certification_pydantic = ShowCertification.model_validate(certification, from_attributes=True)
                        certification_id = certification.id
                        certification_links = {
                            "self": f'{api_base_url}/certifications/search/by_id/{certification_id}',
                            "update": f'{api_base_url}/certifications/update',
                            "delete": f'{api_base_url}/certifications/delete/{certification_id}',
                            "certifications": f'{api_base_url}/certifications',
                            "subjects_in_cycle_hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{certification_id}'
                        }
                        certification_with_links = ShowCertificationWithHATEOAS(certification=certification_pydantic, links=certification_links)
                        certifications_with_hateoas.append(certification_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/certifications/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/certifications/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowCertificationListWithHATEOAS(certifications=certifications_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение сертификаций отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")
                
                
    async def _get_certifications_by_ids(self, ids: list[int], page: int, limit: int, request: Request, db) -> ShowCertificationListWithHATEOAS:
        async with db as session:
            async with session.begin():
                certification_dal = CertificationDAL(session)
                try:
                    certifications_list = await certification_dal.get_certifications_by_ids(ids, page, limit)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    certifications_with_hateoas = []
                    for certification in certifications_list:
                        certification_pydantic = ShowCertification.model_validate(certification, from_attributes=True)
                        certification_id = certification.id
                        certification_links = {
                            "self": f'{api_base_url}/certifications/search/by_id/{certification_id}',
                            "subjects_in_cycle_hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{certification_id}', 
                        }
                        certification_with_links = ShowCertificationWithHATEOAS(certification=certification_pydantic, links=certification_links)
                        certifications_with_hateoas.append(certification_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/certifications/search/by_ids?page={page}&limit={limit}&ids={",".join(map(str, ids))}',
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowCertificationListWithHATEOAS(certifications=certifications_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение сертификаций по списку id отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _delete_certification(self, certification_id: int, request: Request, db) -> ShowCertificationWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    certification_dal = CertificationDAL(session)
                    
                    if not await ensure_certification_exists(certification_dal, certification_id):
                        raise HTTPException(status_code=404, detail=f"Сертификация с id {certification_id} не найдена")

                    certification = await certification_dal.delete_certification(certification_id)
                    
                    if not certification:
                        raise HTTPException(status_code=404, detail=f"Сертификация с id {certification_id} не найдена")

                    certification_pydantic = ShowCertification.model_validate(certification, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "certifications": f'{api_base_url}/certifications',
                        "create": f'{api_base_url}/certifications/create',
                        "subjects_in_cycle_hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{certification_id}'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowCertificationWithHATEOAS(certification=certification_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при удалении сертификации {certification_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении сертификации.")


    async def _update_certification(self, body: UpdateCertification, request: Request, db) -> ShowCertificationWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["certification_id"]}

                    certification_dal = CertificationDAL(session)

                    if not await ensure_certification_exists(certification_dal, body.certification_id):
                        raise HTTPException(status_code=404, detail=f"Сертификация с id {body.certification_id} не найдена")

                    certification = await certification_dal.update_certification(target_id=body.certification_id, **update_data)
                    if not certification:
                        raise HTTPException(status_code=404, detail=f"Сертификация с id {body.certification_id} не найдена")

                    certification_id = certification.id
                    certification_pydantic = ShowCertification.model_validate(certification, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/certifications/search/by_id/{certification_id}',
                        "update": f'{api_base_url}/certifications/update',
                        "delete": f'{api_base_url}/certifications/delete/{certification_id}',
                        "certifications": f'{api_base_url}/certifications',
                        "subjects_in_cycle_hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_id/{certification_id}'
                    }

                    return ShowCertificationWithHATEOAS(certification=certification_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.warning(f"Изменение данных о сертификации отменено (Ошибка: {e})")
                raise e
            