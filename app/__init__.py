from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config=None):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///secure_locker.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB
    app.config['ML_MODEL_PATH'] = os.path.join(os.path.dirname(__file__), '..', 'ml_engine', 'models')

    if config:
        app.config.update(config)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['ML_MODEL_PATH'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'

    # ── Register Blueprints ──────────────────────────────────────────────
    from app.auth import auth as auth_bp
    from app.locker import locker as locker_bp
    from app.admin import admin as admin_bp
    from app.sharing import sharing as sharing_bp
    from app.preview import preview as preview_bp
    from app.api import api as api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(locker_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(sharing_bp, url_prefix='/share')
    app.register_blueprint(preview_bp)
    app.register_blueprint(api_bp)

    # ── WebSocket (SocketIO) ─────────────────────────────────────────────
    from app.notifications import init_socketio
    socketio = init_socketio(app)
    app._socketio = socketio  # store reference for run.py

    with app.app_context():
        db.create_all()
        _seed_admin()

    return app


def _seed_admin():
    from app.models import User
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@securelocker.local', is_admin=True)
        admin.set_password('Admin@1234')
        db.session.add(admin)
        db.session.commit()
