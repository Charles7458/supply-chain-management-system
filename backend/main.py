from fastapi import FastAPI
from routes.inventory import router as inv_router
from routes.dashboard import router as dash_router
from routes.policy import router as policy_router
from routes.forecast import router as forecast_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.include_router(inv_router)
app.include_router(dash_router)
app.include_router(policy_router)
app.include_router(forecast_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)