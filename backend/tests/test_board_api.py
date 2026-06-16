from sqlalchemy import select

from models import Board, Card, Column, User


def test_default_board_loads_with_columns_and_cards(client):
    response = client.get("/api/users/user/board")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "board_default"
    assert [column["title"] for column in data["columns"]] == [
        "Backlog",
        "Discovery",
        "In Progress",
        "Review",
        "Done",
    ]
    assert len(data["cards"]) == 8
    assert data["columns"][0]["cardIds"] == ["card-1", "card-2"]


def test_create_user_creates_separate_empty_board(client, db_session):
    response = client.post(
        "/api/users",
        json={"username": "second", "password": "password"},
    )

    assert response.status_code == 201
    user = response.json()
    # Verify a board was created in the DB for the new user
    from models import Board
    from sqlalchemy import select
    board = db_session.scalar(select(Board).where(Board.user_id == user["id"]))
    assert board is not None
    assert board.user_id == user["id"]


def test_duplicate_username_returns_400(client):
    response = client.post(
        "/api/users",
        json={"username": "user", "password": "password"},
    )

    assert response.status_code == 400


def test_update_board_title_persists(client, db_session):
    response = client.put("/api/users/user/board", json={"title": "Launch Plan"})

    assert response.status_code == 200
    assert response.json()["title"] == "Launch Plan"
    assert db_session.get(Board, "board_default").title == "Launch Plan"


def test_rename_column_persists(client, db_session):
    response = client.put(
        "/api/boards/board_default/columns/col-backlog",
        json={"title": "Ideas"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Ideas"
    assert db_session.get(Column, "col-backlog").title == "Ideas"


def test_create_update_and_delete_card(client, db_session):
    create_response = client.post(
        "/api/columns/col-backlog/cards",
        json={"title": "Write tests", "details": "Cover API CRUD."},
    )

    assert create_response.status_code == 201
    card = create_response.json()
    assert card["position"] == 2

    update_response = client.put(
        f"/api/cards/{card['id']}",
        json={"title": "Write backend tests", "details": "CRUD coverage."},
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Write backend tests"

    delete_response = client.delete(f"/api/cards/{card['id']}")
    assert delete_response.status_code == 200
    assert db_session.get(Card, card["id"]) is None


def test_move_card_between_columns_reorders_both_columns(client):
    response = client.patch(
        "/api/cards/card-1/move",
        json={"column_id": "col-review", "position": 0},
    )

    assert response.status_code == 200
    assert response.json()["columnId"] == "col-review"
    assert response.json()["position"] == 0

    board = client.get("/api/users/user/board").json()
    backlog = next(column for column in board["columns"] if column["id"] == "col-backlog")
    review = next(column for column in board["columns"] if column["id"] == "col-review")
    assert backlog["cardIds"] == ["card-2"]
    assert review["cardIds"][0] == "card-1"


def test_missing_resources_return_404(client):
    assert client.get("/api/users/missing/board").status_code == 404
    assert client.put("/api/cards/missing", json={"title": "Nope"}).status_code == 404
    assert client.delete("/api/cards/missing").status_code == 404


def test_cascade_delete_removes_board_columns_and_cards(db_session):
    user = db_session.get(User, "user_default")
    db_session.delete(user)
    db_session.commit()

    assert db_session.get(Board, "board_default") is None
    assert db_session.scalar(select(Column).where(Column.board_id == "board_default")) is None
    assert db_session.scalar(select(Card).where(Card.id == "card-1")) is None

