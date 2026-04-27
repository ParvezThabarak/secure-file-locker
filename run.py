from app import create_app

app = create_app()

if __name__ == '__main__':
    # Use SocketIO runner for WebSocket support
    if hasattr(app, '_socketio'):
        app._socketio.run(app, debug=True, host='0.0.0.0', port=5000,
                          allow_unsafe_werkzeug=True)
    else:
        app.run(debug=True, host='0.0.0.0', port=5000)
