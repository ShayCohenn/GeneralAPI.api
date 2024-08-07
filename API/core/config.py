import os
from dotenv import load_dotenv

load_dotenv() 

class APIConfig:
    DAD_JOKES_API = os.getenv("DAD_JOKES_API")
    YO_MOMMA_API = os.getenv("YO_MOMMA_API")
    CHUCK_NORRIS_API = os.getenv("CHUCK_NORRIS_API")
    FACTS_API = os.getenv("FACTS_API")
    RIDDLES_API = os.getenv("RIDDLES_API")

class WeatherConfig:
    WEATHER_API_KEY = os.getenv("OPEN_WEATHER_API")
    WEATHER_API_URL = os.getenv("WEATHER_API_URL")

class MongoDBConfig:
    MONGODB_URI = os.getenv("MONGODB_URI")

class SMSConfig:
    SMS_SECRET = os.getenv('SMS_SECRET')
    SMS_KEY = os.getenv('SMS_KEY')

class EmailConfig:
    FROM_EMAIL = os.getenv('FROM_EMAIL')
    PASSWORD = os.getenv('PASSWORD')

class RedisConfig:
    REDIS_URL = os.getenv('REDIS_URL')
    REDIS_PORT = int(os.getenv('REDIS_PORT'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

class AppConfig:
    MODE = os.getenv('MODE')

# -------------------------------------------------------------------------- URLS -------------------------------------------------------------------

_LOCAL_URL = "127.0.0.1:8000"
_PRODUCTION_URL = "https://general-api.vercel.app/"

class URLS:
    API_URL = _PRODUCTION_URL if AppConfig.MODE == "production" else _LOCAL_URL
    FRONTEND_URL = "http://127.0.0.1:3000"
    GOOGLE_REDIRECT_URI = f"{FRONTEND_URL}/auth/google"

# ------------------------------------------------------------------- Messages ----------------------------------------------------------------------

class Messages:
    MAIN_ERROR_MESSAGE = {"error":"an error has occured please try again later, if this error persists please contact 'shay91847@gmail.com'"}
    MAIN_404_MESSAGE = {"error":"Could not find this endpoint. Visit our documentation website at /docs"}

# ------------------------------------------------------------------- Docs --------------------------------------------------------------------------

class Docs:
    VERSION = "0.0.2"

    DESCRIPTION = """
    # Welcome to GeneralAPI's documentation site.

    GeneralAPI is an all purpose API built by the FastAPI framework.
    GeneralAPI is very easy to use, just make a request to an endpoint of your choosing and get JSON in response.
    In GeneralAPI you can get anything for your next project,
    from financial data, generating QR codes, weather data, upcoming sports matches, email and sms sending services
    and even random dad jokes, facts and riddles

    ## Usage:
    All GeneralAPI's services are free to use, but the SMS and Email services require authentication and an API key,
    Just register using the /auth/register endpoint and providing an email, username and a password.

    Then all you need to do is to go to your email and click on the URL to verify you email and get your API key.

    If you lost your API key just login to your account using your username and password and you'll get your API key

    ### Disclaimer:
    As of version 0.0.2 you can only have 1 API key per account
    """