from flask import Flask, jsonify
from flask_cors import CORS
from routes.appointments import bp as appointments_bp
from routes.availability import bp as availability_bp
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(appointments_bp)
    app.register_blueprint(availability_bp)
    
    @app.route('/api/health')
    def health_check():
        return jsonify({"status": "healthy"})
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
