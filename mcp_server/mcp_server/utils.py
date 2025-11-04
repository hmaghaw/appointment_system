import os
import time
import logging
from datetime import datetime
import jwt
import pytz
from zoneinfo import ZoneInfo  # Python 3.9+
from dotenv import load_dotenv
from pathlib import Path

logger = logging.getLogger(__name__)

def generate_jwt_token(validity=8640):
    """
    Generate JWT token for API authentication with time synchronization handling.
    
    Args:
        validity: Token validity in seconds (default: 24 hours)
        
    Returns:
        str: JWT token string
        
    Raises:
        ValueError: If JWT_SECRET_KEY is not set
        Exception: For any other error during token generation
    """
    try:
        if not os.getenv("JWT_SECRET_KEY"):
            env_path = Path(__file__).resolve().parents[2] / ".env"
            if env_path.exists():
                load_dotenv(env_path)

        SECRET_KEY = os.getenv('JWT_SECRET_KEY')
        if not SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY is not set in environment variables")
            
        # Get current time with a small buffer (60 seconds) to account for clock skew
        current_time = int(time.time())
        iat = current_time - 60  # Subtract 60 seconds to handle minor clock differences
        
        payload = {
            'user_id': 999,
            'email': "hanyelgaml@ideationmax.com",
            'business_id': 999,
            'role': "admin",
            'exp': current_time + validity,
            'iat': iat,
            'nbf': iat  # Not Before - token is valid from this time
        }
        
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        logger.debug("Successfully generated JWT token")
        
        # Verify the token can be decoded (sanity check)
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'], options={"verify_exp": False})
            logger.debug(f"Token generated successfully. Expires at: {datetime.fromtimestamp(decoded['exp'])}")
        except Exception as e:
            logger.error(f"Generated token failed validation: {e}")
            raise Exception(f"Failed to validate generated token: {e}")
            
        return token
        
    except jwt.PyJWTError as e:
        error_msg = f"JWT token generation failed: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error generating JWT token: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

def get_today_and_time(timezone_str='US/Eastern', get_translation=None):
    """
    Get current date and time in a formatted string.

    Args:
        timezone_str: Timezone string (default: 'US/Eastern')
        get_translation: Optional translation function for day, month, and AM/PM

    Returns:
        str: Formatted date and time string
    """
    timezone = pytz.timezone(timezone_str)
    now = datetime.now(timezone)

    # Use translation function if provided, otherwise use default string
    def translate(text):
        return get_translation(text) if get_translation else text

    day_of_week = translate(now.strftime('%A'))
    month = translate(now.strftime('%B'))
    day = now.day
    year = now.year
    hour_12 = int(now.strftime('%I'))  # integer hour without leading zero
    minute = now.strftime('%M')
    am_pm = translate(now.strftime('%p'))

    return f"{day_of_week}, {year}-{month}-{day}, {hour_12}:{minute} {am_pm}"

def convert_24_to_12(time_24, get_translation=None):
    """
    Convert 24-hour time format to 12-hour format.

    Args:
        time_24: Time string in 24-hour format (HH:MM)
        get_translation: Optional translation function for AM/PM

    Returns:
        str: Time in 12-hour format with AM/PM
    """
    # Parse 24-hour time with seconds
    t = datetime.strptime(time_24, "%H:%M")
    # Format to 12-hour time without seconds, with AM/PM
    formatted = t.strftime("%I:%M %p")

    # Apply translations if get_translation is provided
    if get_translation:
        formatted = formatted.replace("AM", get_translation("AM"))
        formatted = formatted.replace("PM", get_translation("PM"))

    # Remove leading zero from hour
    if formatted.startswith('0'):
        formatted = formatted[1:]
    return formatted

def convert_datetime(date_str: str, tz_name: str) -> str:
    """
    Convert a GMT date string like 'Mon, 18 Aug 2025 12:04:36 +0000'
    into a formatted datetime string 'YYYY-MM-DD HH:MM:SS'
    in the passed timezone (e.g., 'America/Toronto').
    """
    # Parse input string as datetime (with UTC offset)
    dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")

    # Convert to target timezone
    dt_local = dt.astimezone(ZoneInfo(tz_name))

    # Return formatted datetime string
    return dt_local.strftime("%Y-%m-%d %H:%M:%S")