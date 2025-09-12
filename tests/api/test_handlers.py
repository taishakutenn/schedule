import pytest

# Import fakers functions and get them aliases for convenience
from utils.fakers import get_random_fake_line as get_fake_fio
from utils.fakers import generate_fake_phone_number as gen_fake_number
from utils.fakers import generate_fake_email

from config.settings import ROOT_PATH

# Converting a path object to a string
ROOT_PATH = str(ROOT_PATH)

# Create paths to files with fake data
FAKES_NAMES_PATH = ROOT_PATH + "/utils/fake_data/fake_names.txt"
FAKES_SURNAMES_PATH = ROOT_PATH + "/utils/fake_data/fake_surnames.txt"
FAKES_FATHERNAMES_PATH = ROOT_PATH + "/utils/fake_data/fake_fathernames.txt"


#############################
# TESTS FOR TEACHERS HANDLERS
#############################

# Test checks the api function using 2 sets of data
@pytest.mark.parametrize("name, surname, fathername, phone_number, email", [
    (
            get_fake_fio(FAKES_NAMES_PATH),
            get_fake_fio(FAKES_SURNAMES_PATH),
            get_fake_fio(FAKES_FATHERNAMES_PATH),
            gen_fake_number(),
            generate_fake_email(15)
    ),
    (
            get_fake_fio(FAKES_NAMES_PATH),
            get_fake_fio(FAKES_SURNAMES_PATH),
            get_fake_fio(FAKES_FATHERNAMES_PATH),
            gen_fake_number(),
            generate_fake_email(10)
    ),
    (
            get_fake_fio(FAKES_NAMES_PATH),
            get_fake_fio(FAKES_SURNAMES_PATH),
            get_fake_fio(FAKES_FATHERNAMES_PATH),
            gen_fake_number(),
            generate_fake_email(10)
    ),
    (
            get_fake_fio(FAKES_NAMES_PATH),
            get_fake_fio(FAKES_SURNAMES_PATH),
            get_fake_fio(FAKES_FATHERNAMES_PATH),
            gen_fake_number(),
            generate_fake_email(10)
    )
])
@pytest.mark.asyncio
async def test_create_new_teacher(client, name, surname, fathername, phone_number, email):
    payload = {
        "name": name,
        "surname": surname,
        "fathername": fathername,
        "phone_number": phone_number,
        "email": email
    }

    # Create request for api route
    response = await client.post("/teachers/create", json=payload)
    data = response.json()

    print("Response status:", response.status_code)
    print("Response body:", data)

    # Check result data
    assert data["teacher"]["name"] == payload["name"]
    assert data["teacher"]["surname"] == payload["surname"]
    assert data["teacher"]["fathername"] == payload["fathername"]
    assert data["teacher"]["phone_number"] == payload["phone_number"]
    assert data["teacher"]["email"] == payload["email"]
    # Check HATEOAS links exist
    assert "links" in data
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
