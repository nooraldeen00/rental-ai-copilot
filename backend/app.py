from fastapi import FastAPI
from backend.routes.quote import router as quote_router

app = FastAPI(title="Point of Rental - Quote Copilot")
app.include_router(quote_router)
