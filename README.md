# Django Chat API + Notification Service

A real-time chat backend with WebSocket support, direct messages, group rooms, in-app and email notifications.

## Tech Stack
- **Django** + **Django REST Framework** — REST API
- **Django Channels** — WebSocket real-time messaging
- **Redis** — Channel layer + notification queue
- **PostgreSQL** — Primary database
- **Simple JWT** — Authentication
- **Celery** — Async email notifications

## Project Structure
```
chat_api/
├── manage.py
├── requirements.txt
├── .env.example
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── users/           # Auth, user profiles
│   ├── chat/            # Rooms, messages (DM + group)
│   └── notifications/   # In-app + email notifications
└── docker-compose.yml
```

## Quick Start

### 1. Clone & setup environment
```bash
git clone <repo>
cd chat_api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in your values
```

### 2. Start services (Redis + Postgres)
```bash
docker-compose up -d
```

### 3. Run migrations & start server
```bash
python manage.py migrate
python manage.py runserver

# In another terminal — start Celery worker
celery -A config worker -l info
```

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register new user |
| POST | `/api/auth/login/` | Login, returns JWT tokens |
| POST | `/api/auth/refresh/` | Refresh access token |
| POST | `/api/auth/logout/` | Blacklist refresh token |

### Rooms
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/rooms/` | List rooms you belong to |
| POST | `/api/rooms/` | Create a group room |
| GET | `/api/rooms/<id>/` | Room detail |
| POST | `/api/rooms/<id>/join/` | Join a room |
| POST | `/api/rooms/<id>/leave/` | Leave a room |
| POST | `/api/rooms/dm/` | Get or create DM room with a user |

### Messages
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/rooms/<id>/messages/` | List messages (paginated) |
| POST | `/api/rooms/<id>/messages/` | Send a message |
| DELETE | `/api/messages/<id>/` | Delete your message |

### Notifications
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notifications/` | List your notifications |
| POST | `/api/notifications/<id>/read/` | Mark as read |
| POST | `/api/notifications/read-all/` | Mark all as read |
| GET | `/api/notifications/unread-count/` | Get unread count |

## WebSocket

Connect to: `ws://localhost:8000/ws/chat/<room_id>/`

Include JWT token as query param: `?token=<access_token>`

### Events sent by client
```json
{ "type": "send_message", "content": "Hello!" }
{ "type": "typing", "is_typing": true }
```

### Events received from server
```json
{ "type": "new_message", "message": { "id": 1, "content": "Hello!", "sender": {...}, "created_at": "..." } }
{ "type": "user_typing", "user_id": 2, "username": "alice", "is_typing": true }
{ "type": "notification", "notification": { "id": 1, "message": "...", "unread_count": 3 } }
```
