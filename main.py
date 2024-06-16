from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from constants import MAIN_404_MESSAGE, MAIN_ERROR_MESSAGE, VERSION, DESCRIPTION, r
from api.qr_endpoints import router as qr_router
from api.finance_endpoints import router as stocks_router
from api.other_endpoints import router as other_router
from api.weather.endpoints import router as weather_router
from api.sports.endpoints import router as sports_router
from api.geo.endpoints import router as geo_router
from api.auth.endpoints import router as auth_router
from api.sms_endpoints import router as sms_router
from api.email.endpoints import router as email_router

# ----------------------------------------------- App Initialization ----------------------------------------------------------------------

app = FastAPI(title="GeneralAPI",description=DESCRIPTION, version=VERSION)

# ----------------------------------------------- Enable CORS for all origins -------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(404)
async def custom_404_handler(_, __):
    return ORJSONResponse(status_code=404, content=MAIN_404_MESSAGE)

@app.exception_handler(500)
async def custom_500_handler(_, __):
    return ORJSONResponse(status_code=500, content=MAIN_ERROR_MESSAGE)

# ----------------------------------------------- Including The Routers -------------------------------------------------------------------

app.include_router(auth_router, prefix="/auth")
app.include_router(email_router, prefix="/email")
app.include_router(sms_router, prefix="/sms")
app.include_router(qr_router, prefix="/qr")
app.include_router(stocks_router, prefix="/finance")
app.include_router(geo_router, prefix="/geo")
app.include_router(weather_router, prefix="/weather")
app.include_router(sports_router, prefix="/sports")
app.include_router(other_router, prefix="/other")