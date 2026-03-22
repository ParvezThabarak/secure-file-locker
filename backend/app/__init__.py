from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
from app.config.config import config
from app.database.database import db

# Initialize extensions
login_manager = LoginManager()
cors = CORS()

def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))
    
    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import request, jsonify
        # For API requests, return JSON instead of redirecting
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Authentication required'}), 401
        # For non-API requests, redirect to login
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.files import files_bp
    from routes.profile import profile_bp
    from routes.aws_credentials import aws_credentials_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(files_bp, url_prefix='/api/files')
    app.register_blueprint(profile_bp, url_prefix='/api/profile')
    app.register_blueprint(aws_credentials_bp, url_prefix='/api/aws')
    
    from routes.analytics import analytics_bp
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'S3 File Manager API', 'version': '1.0.0'}
    
    # API root endpoint
    @app.route('/api')
    def api_root():
        return {
            'message': 'S3 File Manager API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'files': '/api/files',
                'profile': '/api/profile',
                'aws': '/api/aws'
            }
        }
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Endpoint not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    # Structured JSON logging for ELK Stack / Kibana
    import logging, sys
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '{"time": "%(asctime)s", "level": "%(levelname)s", '
        '"module": "%(name)s", "message": "%(message)s"}'
    ))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    return app
