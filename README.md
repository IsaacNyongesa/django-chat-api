# Django Chat API + Notification Service

A real-time chat backend built with Django and Django REST Framework. It supports direct messaging, group chat rooms, WebSocket communication, user authentication, backend notification management, and asynchronous email notifications.

The project uses PostgreSQL for persistent storage, Redis for real-time communication and background task infrastructure, Django Channels for WebSockets, and Celery for asynchronous processing.

## Features

- JWT-based user authentication.
- User registration, login, token refresh, and logout.
- Direct messaging between users.
- Group chat room creation and membership management.
- Real-time message delivery using WebSockets.
- Typing indicators.
- **Cursor-based pagination** — Efficiently navigates growing message and notification lists, with a default page size of 50 records.
- Message deletion.
- Backend in-app notification management through REST APIs.
- Real-time notification events through WebSockets.
- Asynchronous email notifications using Celery.
- Redis-backed channel layer.
- PostgreSQL database integration.
- Docker-based development and testing.
- Automated tests using pytest and pytest-django.
- Liveness and readiness endpoints for application monitoring.

## Technology Stack

| Technology            | Purpose                               |
| --------------------- | ------------------------------------- |
| Python 3.12           | Backend programming language          |
| Django 4.2            | Web framework                         |
| Django REST Framework | REST API development                  |
| Django Channels       | WebSocket communication               |
| PostgreSQL 15         | Primary relational database           |
| Redis 7               | Channel layer and task infrastructure |
| Celery                | Asynchronous background processing    |
| Daphne                | ASGI application server               |
| Simple JWT            | JWT authentication                    |
| pytest                | Automated testing                     |
| Docker                | Containerization                      |
| Docker Compose        | Multi-service orchestration           |

## Project Structure

```text
django-chat-api/
|-- apps/
|   |-- chat/
|   |   |-- migrations/
|   |   |-- tests/
|   |   |   |-- test_consumers.py
|   |   |   |-- test_rooms_and_messages.py
|   |   |-- consumers.py
|   |   |-- middleware.py
|   |   |-- models.py
|   |   |-- routing.py
|   |   |-- serializers.py
|   |   |-- urls.py
|   |   |-- views.py
|   |-- notifications/
|   |   |-- migrations/
|   |   |-- tests/
|   |   |   |-- test_notifications.py
|   |   |-- models.py
|   |   |-- tasks.py
|   |   |-- urls.py
|   |   |-- views.py
|   |-- users/
|   |   |-- migrations/
|   |   |-- tests/
|   |   |   |-- test_auth.py
|   |   |-- factories.py
|   |   |-- models.py
|   |   |-- serializers.py
|   |   |-- urls.py
|   |   |-- views.py
|   |-- common/
|       |-- exceptions.py
|       |-- health.py
|       |-- logging.py
|       |-- middleware.py
|       |-- pagination.py
|-- config/
|   |-- settings/
|   |   |-- base.py
|   |   |-- dev.py
|   |   |-- prod.py
|   |   |-- test.py
|   |-- asgi.py
|   |-- celery.py
|   |-- urls.py
|   |-- wsgi.py
|-- .github/
|   |-- workflows/
|       |-- ci.yml
|-- conftest.py
|-- manage.py
|-- Dockerfile
|-- docker-compose.yml
|-- requirements.txt
|-- requirements-dev.txt
|-- pytest.ini
|-- pyproject.toml
|-- .env.example
|-- .dockerignore
|-- .gitignore
```

## Getting Started

### Prerequisites

Install the following:

- Python 3.12 or later
- Docker Desktop (including Docker Compose)
- Git

### 1. Clone the repository

```bash
git clone https://github.com/IsaacNyongesa/django-chat-api.git
cd django-chat-api
```

### 2. Configure environment variables

Create your local environment file from the example:

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

**Linux/macOS**

```bash
cp .env.example .env
```

Review `.env` and configure the values for your local environment.

Do not commit `.env` or expose real credentials.

### 3. Start the application

Build and start the services:

```bash
docker compose up --build -d
```

The Docker Compose configuration starts:

- Django application served by Daphne.
- PostgreSQL database.
- Redis.
- Celery worker.

The application performs database migrations during startup.

### 4. Verify running services

```bash
docker compose ps
```

Check application logs:

```bash
docker compose logs app
```

Check the application health endpoint (liveness):

```text
http://localhost:8000/healthz/
```

Check application readiness, including database and Redis connectivity:

```text
http://localhost:8000/readyz/
```

### 5. Stop the services

```bash
docker compose down
```

To remove the PostgreSQL data volume as well:

```bash
docker compose down -v
```

**Warning:** The second command permanently removes the database volume and its stored data.

## Running Tests

The project includes a dedicated Docker test stage with development dependencies.

Build the test image:

```bash
docker compose build test
```

Run the automated test suite:

```bash
docker compose run --rm test
```

The test configuration uses:

- Django test settings (`config.settings.test`).
- PostgreSQL through the Docker Compose database service.
- An in-memory Channels layer.
- Eager Celery task execution.
- An in-memory email backend.
- A faster password hasher for testing.

The test container runs the suite using pytest and the project's configured test settings.

### Test Results

The project has successfully completed an automated test run:

```text
27 passed
```

This result represents the recorded test run, not a guarantee that every possible application scenario has been tested.

## API Endpoints

The following endpoints describe the application's documented API interface. Consult the Django URL configuration for the current implementation.

### Authentication

Base path: `/api/auth/`

| Method    | Endpoint                               | Description                                                  |
| --------- | -------------------------------------- | ------------------------------------------------------------ |
| POST      | `/api/auth/register/`                  | Register a new user and return access and refresh JWT tokens |
| POST      | `/api/auth/login/`                     | Authenticate a user and obtain JWT tokens                    |
| POST      | `/api/auth/refresh/`                   | Refresh an access token                                      |
| POST      | `/api/auth/logout/`                    | Log out by blacklisting a refresh token                      |
| GET       | `/api/auth/me/`                        | Retrieve the authenticated user's profile                    |
| PUT/PATCH | `/api/auth/me/`                        | Update the authenticated user's profile                      |
| GET       | `/api/auth/users/search/?q=<username>` | Search users by username, returning up to 20 results         |
|           |

### Rooms

| Method | Endpoint                 | Description                         |
| ------ | ------------------------ | ----------------------------------- |
| GET    | `/api/rooms/`            | List rooms available to the user    |
| POST   | `/api/rooms/`            | Create a group room                 |
| GET    | `/api/rooms/<id>/`       | Retrieve room details               |
| POST   | `/api/rooms/<id>/join/`  | Join a group room                   |
| POST   | `/api/rooms/<id>/leave/` | Leave a room                        |
| POST   | `/api/rooms/dm/`         | Get or create a direct-message room |

### Messages

| Method | Endpoint                    | Description                                          |
| ------ | --------------------------- | ---------------------------------------------------- |
| GET    | `/api/rooms/<id>/messages/` | Retrieve room messages                               |
| POST   | `/api/rooms/<id>/messages/` | Send a message                                       |
| DELETE | `/api/messages/<id>/`       | Soft-delete a message sent by the authenticated user |

### Notifications

| Method | Endpoint                           | Description                        |
| ------ | ---------------------------------- | ---------------------------------- |
| GET    | `/api/notifications/`              | List notifications                 |
| POST   | `/api/notifications/<id>/read/`    | Mark a notification as read        |
| POST   | `/api/notifications/read-all/`     | Mark all notifications as read     |
| GET    | `/api/notifications/unread-count/` | Retrieve unread notification count |

## WebSocket Communication

The application uses Django Channels and Daphne to support real-time communication.

### Connection

```text
ws://localhost:8000/ws/chat/<room_id>/?token=<access_token>
```

The WebSocket connection uses a JWT access token for authentication.
The JWT access token is supplied through the `token` query parameter. The WebSocket middleware validates the token, and the consumer checks that the authenticated user belongs to the requested room before accepting the connection.

### Client Events

Send a message:

```json
{
  "type": "send_message",
  "content": "Hello!"
}
```

Send a typing indicator:

```json
{
  "type": "typing",
  "is_typing": true
}
```

### Server Events

New message:

```json
{
  "type": "new_message",
  "message": {
    "id": 1,
    "content": "Hello!",
    "sender": {},
    "created_at": "..."
  }
}
```

Typing indicator:

```json
{
  "type": "user_typing",
  "user_id": 2,
  "username": "alice",
  "is_typing": true
}
```

Notification event:

````json
{
  "type": "notification",
  "notification": {
    "id": 1,
    "title": "New message from alice",
    "body": "Hello!",
    "room_id": 1,
    "unread_count": 3,
    "created_at": "2026-11-15T14:30:00+00:00"
  }
}

## Environment and Configuration

The project separates configuration into different Django settings modules:

- `config.settings.base` - Shared application settings.
- `config.settings.dev` - Development configuration.
- `config.settings.prod` - Production configuration.
- `config.settings.test` - Automated testing configuration.

Environment variables are loaded through `python-decouple`.

## Docker Services

| Service         | Purpose                                         |
| --------------- | ----------------------------------------------- |
| `app`           | Django application served through Daphne        |
| `postgres`      | Persistent relational database                  |
| `redis`         | WebSocket channel layer and task infrastructure |
| `celery_worker` | Processes asynchronous background tasks         |
| `test`          | Runs the automated test suite                   |

Host ports configured in the supplied `.env.example`:

- Application: `8000`
- PostgreSQL: `5434`
- Redis: `6380`

The database and Redis containers communicate internally through their Docker Compose service names.

## Continuous Integration

The repository includes a GitHub Actions workflow at:

```text
.github/workflows/ci.yml
````

Refer to the workflow file for the actual CI jobs and checks configured for the project.

## Development Notes

- Keep environment secrets outside version control.
- Use the test settings for automated testing.
- Use Docker Compose to run the application services together.
- Keep test reports and temporary artifacts out of Git.
- Review dependency updates before introducing them into the application.

## License

No license has currently been specified. Contact the project owner for licensing and usage permissions.

## Author

**Isaac Nyongesa**

GitHub: [IsaacNyongesa](https://github.com/IsaacNyongesa)
