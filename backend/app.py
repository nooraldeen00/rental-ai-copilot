from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.quote import router as quote_router
from backend.routes.runs import router as runs_router  # <-- NEW

app = FastAPI(title="Point of Rental - Quote Copilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_origin_regex=r"https://.*\.app\.github\.dev$",  # for Codespaces
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(quote_router)
app.include_router(runs_router)  # <-- NEW
