import pytest


#############################
# TESTS FOR TEACHERS HANDLERS
#############################

@pytest.mark.asyncio
async def test_create_new_teacher(client):
    payload = {
        "name": "name3",
        "surname": "surname3",
        "fathername": "fathername3",
        "phone_number": "phone_number3",
        "email": "email3@gmail.com"
    }

    # Используйте правильный путь. Если префикс /schedule есть, используйте его.
    # response = await client.post("/teachers/create", json=payload) # <-- без /schedule
    response = await client.post("/teachers/create", json=payload)  # <-- с /schedule

    print(f"Status Code: {response.status_code}")
    # Проверим, что статус код успешный, прежде чем пытаться получить JSON
    assert response.status_code == 201, f"Expected 201, got {response.status_code}. Response text: {response.text}"

    try:
        data = response.json()
        print(f"ОТВЕТ АПИ: {data}")
    except ValueError:  # Обрабатываем случай, если ответ не JSON
        pytest.fail(f"Response is not valid JSON. Status: {response.status_code}, Text: {response.text}")

    # Проверки данных
    assert data["teacher"]["name"] == payload["name"]
    assert data["teacher"]["surname"] == payload["surname"]
    assert data["teacher"]["fathername"] == payload["fathername"]
    assert data["teacher"]["phone_number"] == payload["phone_number"]
    assert data["teacher"]["email"] == payload["email"]
    # Проверка наличия HATEOAS ссылок
    assert "links" in data
    assert "self" in data["links"]
    # Добавьте другие проверки по необходимости

# def test_create_new_teacher_error():
#     pass

#
# def test_get_teacher_by_id():
#     pass
#
#
# def test_get_teacher_by_id_error():
#     pass
#
#
# def test_get_teacher_by_name_and_surname():
#     pass
#
#
# def test_get_teacher_by_name_and_surname_error():
#     pass
#
#
# def test_get_all_teachers():
#     pass
#
#
# def test_get_all_teachers_error():
#     pass
#
#
# def test_delete_teacher():
#     pass
#
#
# def test_delete_teacher_error():
#     pass
#
#
# def test_update_teacher():
#     pass
#
#
# def test_update_teacher_error():
#     pass
