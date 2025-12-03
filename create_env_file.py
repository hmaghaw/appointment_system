import boto3
import json
from botocore.exceptions import ClientError
from pathlib import Path

PROD_TEMPLATE = """ENVIRONMENT=production
DEBUG=True

# Stripe Configuration
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
# Database Configuration
DB_HOST=
DB_USER=
DB_PASSWORD=
DB_NAME=appointment_db

# JWT Configuration
JWT_SECRET_KEY=

# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=production
# DEBUG=False  # Set to False in production

# Twilio Configuration
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WEBHOOK_BASE_URL=

# Email
SEND_EMAIL_WEBHOOK=
FROM_EMAIL=
FROM_NAME=

FRONTEND_URL=

OPENAI_API_KEY=
API_BASE_URL=

CLOVER_URL=
CLOVER_APP_ID=
CLOVER_APP_SECRET=

OPENAI_MODEL=gpt-4o-mini
DEFAULT_MAX_TOKENS=12800
DEFAULT_TEMPERATURE=0.7

ELEVENLABS_API_KEY=
ELEVENLABS_AGENT=NO
"""

DEV_TEMPLATE = """ENVIRONMENT=development
# NGROK Configuration
NGROK_AUTHTOKEN=

# Stripe Configuration
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
# Database Configuration
DB_HOST=localhost
DB_USER=user
DB_PASSWORD=password
DB_NAME=appointment_db

# JWT Configuration
JWT_SECRET_KEY=

# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
# SECRET_KEY=your-secret-key-here  # Uncomment and set for production
# DEBUG=False  # Set to False in production

# Twilio Configuration
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WEBHOOK_BASE_URL=

# Email
SEND_EMAIL_WEBHOOK=
FROM_EMAIL=
FROM_NAME=

FRONTEND_URL=

OPENAI_API_KEY=
API_BASE_URL=

CLOVER_URL=
CLOVER_APP_ID=
CLOVER_APP_SECRET=

OPENAI_MODEL=gpt-4o-mini
DEFAULT_MAX_TOKENS=12800
DEFAULT_TEMPERATURE=0.7

ELEVENLABS_API_KEY=
ELEVENLABS_AGENT=NO
"""
def create_env_from_template(secret_data, environment="production", output_file=".env"):
    """
    Create a .env file from a fixed template, filling in values from secret_data if available.

    Args:
        secret_data (dict): Secrets retrieved from AWS Secrets Manager or another source.
        output_file (str): Path to the .env file to create.
    """
    if environment == "production":
        template = PROD_TEMPLATE
    else:
        template = DEV_TEMPLATE
    lines = []
    for line in template.splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, sep, default_val = line.partition("=")
            key = key.strip()
            new_val = secret_data.get(key, default_val)
            lines.append(f"{key}={new_val}")
        else:
            # Keep comments and blank lines intact
            lines.append(line)

    Path(output_file).write_text("\n".join(lines))
    print(f"✅ .env file created at {output_file}")


def get_secret(secret_name, region_name="us-east-1"):
    """
    Retrieve a secret from AWS Secrets Manager.

    Args:
        secret_name (str): The name of the secret in Secrets Manager.
        region_name (str): The AWS region where the secret is stored.

    Returns:
        dict: The secret as a Python dictionary if JSON, otherwise a string.
    """
    # Create a Secrets Manager client
    client = boto3.client("secretsmanager", region_name=region_name)

    try:
        # Fetch the secret value
        response = client.get_secret_value(SecretId=secret_name)

        # Secrets can be either string or binary
        if "SecretString" in response:
            secret_value = response["SecretString"]
            try:
                return json.loads(secret_value)  # Return as dict if JSON
            except json.JSONDecodeError:
                return secret_value  # Return as raw string
        else:
            # Binary secret
            return response["SecretBinary"]

    except ClientError as e:
        print(f"Error retrieving secret '{secret_name}': {e}")
        raise


def write_env_from_secret(secret_data, env_file=".env"):
    """
    Writes secret key/value pairs to a .env file.

    Args:
        secret_data (dict | str): Secret data as dict or JSON string.
        env_file (str): Path to the .env file.
    """
    # Convert JSON string to dict if needed
    if isinstance(secret_data, str):
        try:
            secret_data = json.loads(secret_data)
        except json.JSONDecodeError:
            raise ValueError("Secret data must be a dict or valid JSON string")

    if not isinstance(secret_data, dict):
        raise ValueError("Secret data must be a dictionary")

    # Create .env file content
    lines = [f"{key}={value}" for key, value in secret_data.items()]

    # Write to file
    Path(env_file).write_text("\n".join(lines))
    print(f"✅ .env file created at: {env_file}")


if __name__ == "__main__":
    import sys

    # Default values
    environment = "production"
    output_file = ".env"

    # # Check for command line arguments
    # if len(sys.argv) > 1:
    #     env_arg = sys.argv[1].lower()
    #     if env_arg in ["production", "prod"]:
    #         environment = "production"
    #         print("Using production environment configuration")
    #     elif env_arg in ["development", "dev"]:
    #         print("Using development environment configuration")
    #     else:
    #         print(f"Warning: Unknown environment '{env_arg}'. Using development environment by default.")
    # else:
    #     print("No environment specified. Using development environment by default.")

    # Get secrets and create .env file
    try:
        if environment == "production":
            secret_name = "prod/polydial/keys"
        else:
            secret_name = "dev/polydial/keys"
        secret_data = get_secret(secret_name, "us-east-1")
        create_env_from_template(secret_data, environment, output_file)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
