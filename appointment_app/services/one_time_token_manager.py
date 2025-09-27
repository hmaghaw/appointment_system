import uuid
from datetime import datetime, timedelta
from appointment_app.database import get_db_cursor


class OneTimeTokenManager:

    def add_token(self, business_id: str, provider: str, expiry_minutes: int = 10) -> str:
        """
        Create a new one-time token and insert into DB.
        Returns the token string.
        """
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)

        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO one_time_token (token, business_id, provider, expires_at)
                VALUES (%s, %s, %s, %s)
            """, (token, business_id, provider, expires_at))

        return token

    def consume_token(self, token: str, provider: str):
        """
        Validate a one-time token. If valid, mark it as used.
        Returns business_id if successful, None if invalid/expired.
        Raises exception if a DB error occurs.
        """
        try:
            with get_db_cursor(commit=True) as cursor:
                cursor.execute("""
                               SELECT token, business_id
                               FROM one_time_token
                               WHERE token = %s
                                 AND provider = %s
                                 AND used = FALSE
                                 AND expires_at > NOW() LIMIT 1
                               """, (token, provider))
                row = cursor.fetchone()

                if not row:
                    # Invalid, expired, or already used
                    return None

                # Try to update (consume) the token
                cursor.execute("""
                               UPDATE one_time_token
                               SET used    = TRUE,
                                   used_at = NOW()
                               WHERE token = %s
                               """, (token,))

                return row['business_id']

        except Exception as e:
            # Log it or re-raise depending on your logging setup
            print(f"[consume_token] Error consuming token {token}: {e}")
            raise

    def cleanup_tokens(self):
        """
        Remove expired or already used tokens.
        Run this periodically (cronjob/worker).
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                DELETE FROM one_time_token
                WHERE used = TRUE OR expires_at < NOW()
            """)
