from sqlmodel import Session, SQLModel, create_engine

db_file = "fanta_db.db3"


def create_db(db_file):
    db = create_engine(f"sqlite:///{db_file}", echo=True)
    SQLModel.metadata.create_all(db)
    return db


db = create_db(db_file)


def get_session():
    try:
        session = Session(db)
        yield session
    finally:
        session.close()
        print("Session closed")
