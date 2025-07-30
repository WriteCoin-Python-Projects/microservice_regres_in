from pydantic import BaseModel


# Модель данных
class Item(BaseModel):
    id: str

    class Config:
        extra = "allow"
