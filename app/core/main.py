from fastapi import FastAPI

from API.routers import book

app = FastAPI()

app.include_router(book.router)
