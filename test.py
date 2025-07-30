import json
import os
from typing import Any, Dict
import pytest
import requests
from jsonschema import validate

data_reqres_in: Dict[str, Any] = {}
data_microservice: Dict[str, Any] = {}
file_reqres_in = "data_reqres_in.json"
file_microservice = "data_microservice.json"

if os.path.exists(file_reqres_in):
    with open(file_reqres_in, "r") as file:
        data_reqres_in = json.load(file)

if os.path.exists(file_microservice):
    with open(file_microservice, "r") as file:
        data_microservice = json.load(file)


@pytest.mark.parametrize(
    "user_id, expected_email",
    [
        (2, "janet.weaver@reqres.in"),
    ],
)
def test_reqres_in(user_id: int, expected_email: str):
    url = f"http://localhost:8000/api/users/{user_id}"

    response = requests.get(url)
    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    body = response.json()
    assert "data" in body, "Response body does not contain 'data' key"

    data = body["data"]

    assert data["id"] == user_id, f"Expected id {user_id}, but got {data['id']}"
    assert (
        data["email"] == expected_email
    ), f"Expected email {expected_email}, but got {data['email']}"


def test_microservice():
    response = requests.post(
        "http://localhost:8000/api/items", data={"id": "users/1", "name": "морфеус", "job": "мастер"}
    )
    body = response.json()

    assert response.status_code == 201
    validate(body, schema=data_microservice["users/1"])