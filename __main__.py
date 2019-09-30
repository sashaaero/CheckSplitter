from models import db
from views import app


if __name__ == '__main__':
    db.generate_mapping(create_tables=True)
    app.config.update(DEBUG=True)
    app.run()
