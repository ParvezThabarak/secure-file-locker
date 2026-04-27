"""
WebSocket Real-Time Notifications
===================================
Uses Flask-SocketIO to push live notifications to connected users.
"""
from flask_socketio import SocketIO, join_room, emit
from flask_login import current_user

socketio = SocketIO()


def init_socketio(app):
    """Initialize SocketIO with the Flask app."""
    socketio.init_app(app, async_mode='threading', cors_allowed_origins='*')
    register_handlers()
    return socketio


def register_handlers():
    """Register SocketIO event handlers."""

    @socketio.on('connect')
    def handle_connect():
        if current_user and current_user.is_authenticated:
            join_room(f'user_{current_user.id}')
            if current_user.is_admin:
                join_room('admin_room')

    @socketio.on('disconnect')
    def handle_disconnect():
        pass  # rooms are auto-cleaned


def emit_notification(user_id: int, message: str, notif_type: str = 'info',
                      icon: str = '🔔'):
    """Push a notification to a specific user."""
    try:
        socketio.emit('notification', {
            'message': message,
            'type': notif_type,
            'icon': icon,
        }, room=f'user_{user_id}')
    except Exception:
        pass  # notification failure must never break main flow


def emit_admin_alert(message: str, notif_type: str = 'warning', icon: str = '⚠️'):
    """Broadcast an alert to all connected admin users."""
    try:
        socketio.emit('notification', {
            'message': message,
            'type': notif_type,
            'icon': icon,
        }, room='admin_room')
    except Exception:
        pass
