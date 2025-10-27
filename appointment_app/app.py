from flask import Flask, jsonify, request
from flask_cors import CORS
from appointment_app.config import Config
import os


def create_app(config_dict=None):
    """Create and configure the Flask application.
    
    Args:
        config_dict (dict, optional): Configuration dictionary to update the app config.
        If None, uses default configuration from Config class.
    """
    app = Flask(__name__)
    app.config['JSON_SORT_KEYS'] = False
    app.config.from_object(Config)

    # Update config with provided dictionary if any
    if config_dict:
        app.config.update(config_dict)
    
    # Configure CORS
    CORS(app)
    
    # Initialize SocketIO with the app

    
    # Import and register blueprints
    from appointment_app.routes.appointments import bp as appointments_bp
    from appointment_app.routes.availability import bp as availability_bp
    from appointment_app.routes.business import bp as business_bp
    from appointment_app.routes.service import bp as service_bp
    from appointment_app.routes.customers import bp as customers_bp
    from appointment_app.routes.call_meta import bp as call_history_bp
    from appointment_app.routes.call_conversation import bp as call_conversation_bp
    from appointment_app.routes.translations import bp as translations_bp
    from appointment_app.routes.languages import bp as languages_bp
    from appointment_app.routes.user import bp as user_bp
    from appointment_app.routes.business_hours import bp as business_hours_bp
    from appointment_app.routes.onboarding import bp as onboarding_bp
    from appointment_app.routes.restaurants import bp as restaurants_bp
    from appointment_app.routes.twilio import bp as twilio_bp
    from appointment_app.routes.stripe import bp as stripe_bp
    from appointment_app.routes.subscription import bp as subscription_bp
    from appointment_app.routes.premium_numbers import bp as premium_numbers_bp
    from appointment_app.routes.restaurants import bp as restaurants_bp
    from appointment_app.routes.restaurant_combo import bp as restaurant_combo_bp
    from appointment_app.routes.restaurant_order import bp as restaurant_order_bp
    from appointment_app.routes.clover import bp as clover_bp
    from appointment_app.routes.export import bp as export_bp
    from appointment_app.routes.prompt import prompt_bp
    from appointment_app.routes.restaurant_menu import bp as restaurant_menu_bp
    from appointment_app.routes.restaurant_translation import bp as restaurant_translations_bp
    
    # Register blueprints
    app.register_blueprint(appointments_bp)
    app.register_blueprint(availability_bp)
    app.register_blueprint(business_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(service_bp, url_prefix='/api/services')
    app.register_blueprint(call_history_bp)
    app.register_blueprint(call_conversation_bp)
    app.register_blueprint(translations_bp)
    app.register_blueprint(languages_bp)
    app.register_blueprint(business_hours_bp, url_prefix='/api')
    app.register_blueprint(twilio_bp)  # URL prefix is defined in the Blueprint
    app.register_blueprint(user_bp, url_prefix='/api/auth')
    app.register_blueprint(stripe_bp)  # Stripe webhook and payment endpoints
    app.register_blueprint(subscription_bp, url_prefix='/api/subscriptions')  # Subscription plan endpoints
    app.register_blueprint(premium_numbers_bp, url_prefix='/api')  # Premium numbers endpoints
    app.register_blueprint(restaurants_bp)  # Restaurant endpoints (prefix is defined in the blueprint)
    app.register_blueprint(onboarding_bp)  # Onboarding endpoints
    app.register_blueprint(restaurant_combo_bp)
    app.register_blueprint(restaurant_order_bp)
    app.register_blueprint(clover_bp)  # Clover integration endpoints
    app.register_blueprint(export_bp)
    app.register_blueprint(prompt_bp)
    app.register_blueprint(restaurant_menu_bp)  # Restaurant menu endpoints
    app.register_blueprint(restaurant_translations_bp)  # Restaurant translations endpoint
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Check if the API is running"""
        return jsonify({"status": "healthy"})
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)