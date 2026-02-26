from fastapi import FastAPI, HTTPException
import uvicorn
from interface.delivery import Delivery
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Literal

app = FastAPI()

sessions = {}

connections = {}


class GameDelivery(Delivery):
    pass


@app.get("/")
def qwe():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
