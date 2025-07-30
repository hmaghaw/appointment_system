from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
import os

def create_app(config_dict=None):
    """Create and configure the Flask application.
    
    Args:
        config_dict (dict, optional): Configuration dictionary to update the app config.
        If None, uses default configuration from Config class.
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Update config with provided dictionary if any
    if config_dict:
        app.config.update(config_dict)
    
    # Configure CORS
    CORS(app)
    # CORS(app,
    #      resources={
    #          r"/*": {
    #              "origins": [
    #                  "https://your-spa-frontend.com",
    #                  "https://coffeehome.ca",
    #                  "https://*.replit.app",
    #                  "https://*.replit.dev",
    #                  "http://localhost:*",
    #                  "http://127.0.0.1:*"
    #              ],
    #              "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    #              "allow_headers": ["Content-Type", "Authorization", "X-Domain", "Accept", "Origin"],
    #              "supports_credentials": True
    #          }
    #      })
    
    # Import and register blueprints
    from routes.appointments import bp as appointments_bp
    from routes.availability import bp as availability_bp
    from routes.business import bp as business_bp
    from routes.customers import bp as customers_bp
    from routes.call_meta import bp as call_history_bp
    from routes.call_conversation import bp as call_conversation_bp
    from routes.translations import bp as translations_bp
    from routes.user import bp as user_bp
    from routes.business_hours import bp as business_hours_bp
    
    app.register_blueprint(appointments_bp)
    app.register_blueprint(availability_bp)
    app.register_blueprint(business_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(call_history_bp)
    app.register_blueprint(call_conversation_bp)
    app.register_blueprint(translations_bp)
    app.register_blueprint(business_hours_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api/auth')
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Check if the API is running"""
        return jsonify({"status": "healthy"})
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
