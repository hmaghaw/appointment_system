from flask import Flask, jsonify
from flask_cors import CORS
from config import Config

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
    
    # Enable CORS
    CORS(app)
    
    # Import and register blueprints
    from routes.appointments import bp as appointments_bp
    from routes.availability import bp as availability_bp
    from routes.business import bp as business_bp
    from routes.customers import bp as customers_bp
    from routes.call_history import bp as call_history_bp
    
    app.register_blueprint(appointments_bp)
    app.register_blueprint(availability_bp)
    app.register_blueprint(business_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(call_history_bp)
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Check if the API is running"""
        return jsonify({"status": "healthy"})
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
