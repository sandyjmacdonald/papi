import pytest
import uuid
from papi.project import (
    Project,
    check_project_id,
    check_user_id,
    check_suffix,
    check_uuid,
    THIS_YEAR,
)

valid_project_ids = ["P2024-RST-ABCD", "P2024-RT1-ABCD"]
invalid_project_ids = [
    "2024-RST-ABCD",
    "P2024-RT12-ABCD",
    "P2024-RST-ABC1",
    "R2024-RST-ABCD",
    "P2024_RST_ABCD",
    "P2024RSTABCD",
]

valid_suffixes = ["ABCD", "PQRS", "ZZZZ"]
invalid_suffixes = ["ABC", "PQRST", "AB1", 1234]

valid_uuids = [str(uuid.uuid4()), "2c173903-3b1c-4967-9a70-8f3a4607c06c"]
invalid_uuids = [
    "99a832b1-7c6d-4d06-96ac-a67a68f4a2b",
    "271d761d-d0c8-4e1d-8ef9-99dad705453cd",
]

example_project_id = "P2024-RST-ABCD"
example_year = 2024
example_user_id = "RST"
example_suffix = "ABCD"
example_uuid = "2c173903-3b1c-4967-9a70-8f3a4607c06c"

example_invalid_project_id = "P2024_RST_ABCD"
example_invalid_uuid = "99a832b1-7c6d-4d06-96ac-a67a68f4a2b"


@pytest.fixture
def proj() -> Project:
    return Project(
        year=example_year,
        user_id=example_user_id,
        suffix=example_suffix,
        p_uuid=example_uuid,
    )


def test_check_project_id_valid() -> None:
    for valid_project_id in valid_project_ids:
        assert check_project_id(valid_project_id) is True


def test_check_project_id_invalid() -> None:
    for invalid_project_id in invalid_project_ids:
        assert check_project_id(invalid_project_id) is False


def test_check_suffix_valid() -> None:
    for valid_suffix in valid_suffixes:
        assert check_suffix(valid_suffix) is True


def test_check_suffix_invalid() -> None:
    for invalid_suffix in invalid_suffixes:
        if isinstance(invalid_suffix, str):
            assert check_suffix(invalid_suffix) is False
        else:
            with pytest.raises(TypeError):
                check_suffix(invalid_suffix)


def test_check_uuid_valid() -> None:
    for valid_uuid in valid_uuids:
        assert check_uuid(valid_uuid) is True


def test_check_uuid_invalid() -> None:
    for invalid_uuid in invalid_uuids:
        assert check_uuid(invalid_uuid) is False


def test_create_project(proj) -> None:
    assert proj.id == example_project_id
    assert proj.year == example_year
    assert proj.user_id == example_user_id
    assert proj.suffix == example_suffix
    assert proj.p_uuid == example_uuid


def test_minimal_project() -> None:
    proj = Project(user_id=example_user_id)
    assert proj.year == THIS_YEAR
    assert check_suffix(proj.suffix) is True


def test_preformed_project_id() -> None:
    proj = Project(id=example_project_id)
    assert proj.id_is_valid() is True


def test_malformed_project_id() -> None:
    with pytest.raises(TypeError):
        Project(id=example_invalid_project_id)


def test_incorrect_uuid() -> None:
    with pytest.warns(UserWarning):
        Project(user_id=example_user_id, p_uuid=example_invalid_uuid)


def test_str(proj) -> None:
    assert str(proj) == proj.id


def test_repr(proj) -> None:
    assert repr(proj) == proj.id


def test_project_id_is_valid(proj) -> None:
    assert proj.id_is_valid() is True
