"""
Google OAuth2 callback and email sending routes.
Handles OAuth2 callbacks from Google services and manages email sending.
"""
import os
import json
import logging
import base64
import smtplib
import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, request, jsonify, current_app
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Create blueprint
bp = Blueprint('google', __name__, url_prefix='/rest/oauth2-credential')

# Set up logging
logger = logging.getLogger(__name__)

# OAuth2 Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5000/rest/oauth2-credential/callback')
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

# Token storage (in production, use a database)
token_storage = {}

def get_flow():
    """Create and return a Flow instance for OAuth2"""
    return Flow.from_client_config(
        {
            'web': {
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'redirect_uris': [REDIRECT_URI]
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

class GmailService:
    """Service for sending emails using Gmail API"""
    
    def __init__(self, credentials=None):
        """Initialize with optional credentials"""
        self.credentials = credentials
        self.service = None
        
    def build_service(self):
        """Build the Gmail API service"""
        if not self.credentials:
            raise ValueError("No credentials provided")
            
        creds = Credentials(
            token=self.credentials.get('access_token'),
            refresh_token=self.credentials.get('refresh_token'),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET
        )
        
        # Refresh token if expired
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            
        self.service = build('gmail', 'v1', credentials=creds)
        return self.service
    
    def send_email(self, to_email, subject, body, is_html=True):
        """Send an email using Gmail API"""
        try:
            if not self.service:
                self.build_service()
                
            message = MIMEMultipart('alternative')
            message['to'] = to_email
            message['from'] = f"Elite Wellness Spa <{self.credentials.get('email')}>"
            message['subject'] = subject
            
            # Create the message body
            if is_html:
                part1 = MIMEText(body, 'html')
            else:
                part1 = MIMEText(body, 'plain')
                
            message.attach(part1)
            
            # Encode the message
            encoded_message = (base64.urlsafe_b64encode(message.as_bytes())
                .decode()
                .replace('+', '-')
                .replace('/', '_')
                .replace('=', ''))
            # Send the message
            message = (self.service.users().messages()
                     .send(userId='me', 
                          body={'raw': encoded_message})
                     .execute())
            
            logger.info(f"Email sent to {to_email} with ID: {message['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

@bp.route('/send', methods=['POST'])
def send_email():
    """
    Send an email using the Gmail API.
    
    Request format (JSON):
    {
        "to": "recipient@example.com",
        "subject": "Email Subject",
        "body": "<h1>Hello!</h1><p>This is the email content.</p>",
        "is_html": true,
        "from_email": "sender@example.com",
        "from_name": "Sender Name"
    }
    
    'from_email' and 'from_name' are optional. If not provided, defaults from GmailService will be used.
    'is_html' is optional and defaults to true.
    """
    try:
        if 'credentials' not in token_storage:
            return jsonify({
                'success': False,
                'error': 'not_authenticated',
                'message': 'No OAuth2 credentials found. Please authenticate first.'
            }), 401
            
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['to', 'subject', 'body']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': 'missing_field',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Initialize Gmail service with credentials
        gmail = GmailService(credentials=token_storage['credentials'])
        
        # Set sender information if provided
        from_email = data.get('from_email') or token_storage['credentials'].get('email')
        from_name = data.get('from_name', '')
        
        if from_name and from_email:
            gmail.credentials['email'] = f'"{from_name}" <{from_email}>'
        elif from_email:
            gmail.credentials['email'] = from_email
        
        # Send the email
        success = gmail.send_email(
            to_email=data['to'],
            subject=data['subject'],
            body=data['body'],
            is_html=data.get('is_html', True)
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Email sent successfully',
                'to': data['to'],
                'subject': data['subject']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'email_send_failed',
                'message': 'Failed to send email'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in send_email endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'server_error',
            'message': str(e)
        }), 500

@bp.route('/authorize')
def authorize():
    """Initiate the OAuth2 flow"""
    flow = get_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    return jsonify({
        'authorization_url': authorization_url,
        'state': state
    })

@bp.route('/callback', methods=['GET', 'POST'])
def oauth2_callback():
    """Handle OAuth2 callback from Google"""
    try:
        # Handle both GET and POST requests
        if request.method == 'GET':
            code = request.args.get('code')
            state = request.args.get('state')
        else:
            data = request.get_json()
            code = data.get('code')
            state = data.get('state')

        if not code:
            return jsonify({
                'success': False,
                'error': 'missing_code',
                'message': 'No authorization code provided'
            }), 400

        flow = get_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Store the credentials (in production, use a database)
        token_storage['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }

        # Get user info
        user_info = flow.oauth2session.get('https://www.googleapis.com/oauth2/v2/userinfo').json()
        token_storage['user_info'] = user_info

        return jsonify({
            'success': True,
            'message': 'Successfully authenticated with Google',
            'user_info': user_info
        })

    except Exception as e:
        logger.error(f"Error in OAuth2 callback: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'authentication_failed',
            'message': str(e)
        }), 500

@bp.route('/send-test-email', methods=['POST'])
def send_test_email():
    """Send a test email using stored credentials"""
    try:
        if 'credentials' not in token_storage:
            return jsonify({
                'success': False,
                'error': 'not_authenticated',
                'message': 'No OAuth2 credentials found. Please authenticate first.'
            }), 401

        data = request.get_json()
        to_email = data.get('to')
        subject = data.get('subject', 'Test Email from Google OAuth2')
        body = data.get('body', 'This is a test email sent using Google OAuth2.')

        if not to_email:
            return jsonify({
                'success': False,
                'error': 'missing_recipient',
                'message': 'Recipient email address is required'
            }), 400

        gmail = GmailService(credentials=token_storage['credentials'])
        success = gmail.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            is_html=True
        )

        if success:
            return jsonify({
                'success': True,
                'message': 'Test email sent successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'email_send_failed',
                'message': 'Failed to send test email'
            }), 500

    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'server_error',
            'message': str(e)
        }), 500
