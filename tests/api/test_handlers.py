import pytest


#############################
# TESTS FOR TEACHERS HANDLERS
#############################

def test_create_new_teacher_error():
    pass

def test_create_new_teacher(client):

    # Create test data
    payload = {
        "name": "name3",
        "surname": "surname3",
        "fathername": "fathername3",
        "phone_number": "phone_number3",
        "email": "email3@gmail.com"
    }

    # Get response from server
    response = client.post("/teachers/create", json=payload)

    # Check that status code is 201
    # assert response.status_code == 201
    print(response.status_code)

    # Read response's data
    data = response.json()

    print(f"ОТВЕТ АПИ: {data}")

    # Check response's data for validity
    assert data["teacher"]["name"] == payload["name"]
    assert data["teacher"]["surname"] == payload["surname"]
    assert data["teacher"]["fathername"] == payload["fathername"]
    assert data["teacher"]["phone_number"] == payload["phone_number"]
    assert data["teacher"]["email"] == payload["email"]


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
