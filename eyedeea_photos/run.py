from stream_server.main import socketio, app

if __name__ == '__main__':    
    socketio.run(app, host='0.0.0.0', port=9090, debug=False)
