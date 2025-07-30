import json
import os
from typing import Any, Dict
from pydantic import BaseModel
import atexit
import requests
from fastapi import FastAPI, HTTPException
from enum import Enum

app = FastAPI()


# Модель данных
class Item(BaseModel):
    id: str

    class Config:
        extra = "allow"


data_file = "data.json"

data: Dict[str, Any] = {}


class Case(Enum):
    REGRES_IN = 1
    MICROSERVICE = 2


case_service: Case


def get_case():
    global data_file

    try:
        user_input = int(
            input("Введите числовое значение способа (1: REGRES_IN, 2: MICROSERVICE): ")
        )
        case = Case(user_input)
        print(f"Вы выбрали способ: {case.name}")
    except ValueError:
        print("Пожалуйста, введите корректное числовое значение.")
        return get_case()
    except KeyError:
        print("Некорректное числовое значение. Пожалуйста, попробуйте снова.")
        return get_case()

    match case:
        case Case.REGRES_IN:
            data_file = f"data_regres_in.json"
        case Case.MICROSERVICE:
            data_file = f"data_microservice.json"
        case _:
            raise "Unknown literal"

    return case


def load_data():
    """Загрузка данных из JSON файла при старте"""
    global data
    try:
        if os.path.exists(data_file):
            with open(data_file, "r") as file:
                items = json.load(file)
                data = {item["id"]: Item(**item) for item in items}
        else:
            data = {}
        print(f"Данные успешно загружены, всего элементов: {len(data)}")
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        data = {}


def save_data():
    """Сохранение данных в JSON файл при завершении"""
    try:
        # items = [item for (key, item) in data.items()]
        with open(data_file, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Данные успешно сохранены, всего элементов: {len(data)}")
    except Exception as e:
        print(f"Ошибка при сохранении данных: {e}")


@app.get("/api/{request:path}")
async def request(request: str):
    print("request:", request)
    """Получить элемент по запросу"""
    if request in data:
        return data[request]
    elif case_service == Case.MICROSERVICE:
        print(case_service)
        raise HTTPException(status_code=404, detail="Item not found")
    # отправка запроса
    url = f"https://reqres.in/api/{request}"
    headers = {"x-api-key": "reqres-free-v1"}
    try:
        print("Запрос", url)
        response = requests.get(url, headers=headers, timeout=5)
        print("Ответ", response.text)

        # Проверяем статус ответа
        if response.status_code != 200:
            error_msg = f"Внешний API вернул ошибку: {response.status_code}"
            raise HTTPException(status_code=response.status_code, detail=error_msg)

        # Парсинг JSON ответа
        try:
            body = response.json()
        except ValueError as e:
            error_msg = f"Ошибка парсинга JSON: {str(e)}"
            raise HTTPException(status_code=500, detail=error_msg)

        # Сохранение в кэш и получение результата
        data[request] = body
        return body

    except requests.exceptions.Timeout:
        error_msg = "Таймаут при запросе к внешнему API"
        raise HTTPException(status_code=504, detail=error_msg)
    except requests.exceptions.RequestException as e:
        error_msg = f"Ошибка при запросе к внешнему API: {str(e)}"
        raise HTTPException(status_code=502, detail=error_msg)


@app.post("/api/items/", response_model=Item)
async def create_item(item: Item):
    if case_service != Case.MICROSERVICE:
        raise HTTPException(status_code=403, detail="Forbidden")
    """Создать новый элемент"""
    if item.id in data:
        raise HTTPException(status_code=400, detail="Item already exists")
    data[item.id] = item
    return item

@app.put("/api/{item_id:path}", response_model=Item)
async def update_item(item_id: int, item: Item):
    if case_service != Case.MICROSERVICE:
        raise HTTPException(status_code=403, detail="Forbidden")
    """Обновить существующий элемент"""
    if item_id not in data:
        raise HTTPException(status_code=404, detail="Item not found")
    data[item_id] = item
    return item

@app.delete("/api/{item_id:path}")
async def delete_item(item_id: str):
    if case_service != Case.MICROSERVICE:
        raise HTTPException(status_code=403, detail="Forbidden")
    """Удалить элемент"""
    if item_id not in data:
        raise HTTPException(status_code=404, detail="Item not found")
    del data[item_id]
    return {"message": "Item deleted"}

@app.get("/status")
def main():
    return "{status:ok}"


if __name__ == "__main__":
    import uvicorn

    # определить способ реализации
    case_service = get_case()

    # Зарегистрируем функцию сохранения при завершении
    atexit.register(save_data)

    # Загружаем данные при старте
    load_data()

    uvicorn.run(app, host="0.0.0.0", port=8000)
