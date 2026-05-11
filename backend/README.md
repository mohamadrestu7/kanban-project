# Backend - Project Management MVP

## Overview

FastAPI-based backend for the Project Management MVP application. Handles API endpoints, database operations, and AI integration.

## Dependencies

- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **sqlalchemy** - ORM for database
- **python-dotenv** - Environment variable loading
- **openai** - OpenAI API client
- **pytest** - Testing framework

## Project Structure

```
backend/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Project configuration
├── tests/
│   ├── conftest.py     # Test configuration and fixtures
│   └── test_main.py    # Unit tests for main endpoints
└── [future modules]
    ├── database.py     # Database setup and session
    ├── models.py       # SQLAlchemy ORM models
    ├── api/
    │   ├── users.py    # User endpoints
    │   ├── boards.py   # Board endpoints
    │   ├── cards.py    # Card endpoints
    │   └── ai.py       # AI/chat endpoints
    └── schemas.py      # Pydantic request/response schemas
```

## Current Endpoints

### `/api/test` [GET]

Test endpoint to verify API is running.

**Response:**

```json
{
  "status": "ok",
  "message": "API is running",
  "version": "0.1.0"
}
```

### `/` [GET]

Serves hello world HTML page with application status and next steps.

## Running the Backend

### With Docker

```bash
docker-compose up
```

### Local Development

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Server runs on http://localhost:8000

## Testing

### Run All Tests

```bash
pytest tests/
```

### Run With Coverage

```bash
pytest tests/ --cov
```

### Run Specific Test

```bash
pytest tests/test_main.py::TestAPIEndpoints::test_api_test_endpoint
```

### Watch Mode

```bash
pytest tests/ --tb=short -v
```

## Environment Variables

- `OPENAI_API_KEY` - OpenAI API key for AI features
- `PORT` - Server port (default: 8000)
- `DATABASE_URL` - Database connection string (future)

## Code Standards

- Use latest Python features (3.12+)
- Keep it simple - no over-engineering
- Async/await for I/O operations
- Proper error handling with appropriate HTTP status codes
- Type hints for all functions
- Comprehensive docstrings for complex logic

## Future Modules

### Database (Part 5-6)

- SQLAlchemy models for User, Board, Column, Card
- Database session management
- Migration strategy with Alembic

### API Routes (Part 6-9)

- User authentication and management
- Board CRUD operations
- Card operations with column management
- AI chat integration with OpenAI

### Schema Validation (Part 7)

- Pydantic models for request/response validation
- Proper error messages for validation failures

### AI Integration (Part 8-9)

- OpenAI API client wrapper
- Structured outputs handling
- Conversation history storage
