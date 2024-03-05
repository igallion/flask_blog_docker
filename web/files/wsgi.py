from app import app
from flask import Flask
from app import init_db, get_db_connection

application = app

if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=80, debug=True)