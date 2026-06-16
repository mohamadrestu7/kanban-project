from models import Board, Card, Column, User


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at,
    }


def serialize_card(card: Card) -> dict:
    return {
        "id": card.id,
        "title": card.title,
        "details": card.details,
        "columnId": card.column_id,
        "position": card.position,
        "created_at": card.created_at,
        "updated_at": card.updated_at,
    }


def serialize_column(column: Column) -> dict:
    return {
        "id": column.id,
        "title": column.title,
        "position": column.position,
        "cardIds": [card.id for card in sorted(column.cards, key=lambda item: item.position)],
        "created_at": column.created_at,
        "updated_at": column.updated_at,
    }


def serialize_board(board: Board) -> dict:
    columns = sorted(board.columns, key=lambda item: item.position)
    cards = {
        card.id: serialize_card(card)
        for column in columns
        for card in sorted(column.cards, key=lambda item: item.position)
    }
    return {
        "id": board.id,
        "title": board.title,
        "userId": board.user_id,
        "columns": [serialize_column(column) for column in columns],
        "cards": cards,
        "created_at": board.created_at,
        "updated_at": board.updated_at,
    }
