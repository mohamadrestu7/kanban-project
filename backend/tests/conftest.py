import sys
from importlib import import_module
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

backend_path = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_path))

database = import_module("database")
main = import_module("main")
seed = import_module("seed")


@pytest.fixture
def db_session(tmp_path: Path) -> Generator[Session]:
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    database.Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    seed.seed_default_data(session)

    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    def override_get_session():
        yield db_session

    main.app.dependency_overrides[database.get_session] = override_get_session
    test_client = TestClient(main.app)

    try:
        yield test_client
    finally:
        main.app.dependency_overrides.clear()
        test_client.close()
