from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.src.api.routers import dev, login, user, access_group

from server.src.database import init_db, engine

app = FastAPI(title="MAGGxDND")

# This will be our sub-application to hold all the prefixed routes
sub_app = FastAPI()
sub_app.include_router(user.router)
sub_app.include_router(access_group.router)
sub_app.include_router(login.router)
sub_app.include_router(dev.router)


app.mount("/api/v1", sub_app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://localhost:3001", "http://localhost:8080"],  # Common development ports
    allow_credentials=True,  # <-- Important for cookies
    allow_methods=["*"],     # <-- Allows all methods (GET, POST, etc.)
    allow_headers=["*"],     # <-- Allows all headers
)

@app.on_event("startup")
def on_startup():
    # Initialize the database tables
    init_db(engine)