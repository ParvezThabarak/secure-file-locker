import os
import sys
from app import create_app
from app.database.database import db
from models.user import User
from models.file import File
from database_setup import setup_database

app = create_app(os.getenv('FLASK_ENV', 'development'))

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'File': File}

if __name__ == '__main__':
    print("🚀 Starting S3 File Manager Backend...")
    
    # Setup database only if not already done (prevents multiple setups on Flask restarts)
    setup_flag_file = '/app/.database_setup_complete'
    if not os.path.exists(setup_flag_file):
        print("🗄️  Running database setup...")
        if not setup_database(app):
            print("❌ Failed to setup database. Exiting...")
            sys.exit(1)
        # Create flag file to indicate setup is complete
        with open(setup_flag_file, 'w') as f:
            f.write('Database setup completed')
        print("✅ Database setup completed")
    else:
        print("✅ Database setup already completed, skipping...")
    
    print("🌐 Starting Flask application...")
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])
