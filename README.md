# 🎬 Videoflix – Streaming Platform

Videoflix is a streaming web app with a Django backend and a simple frontend built with JavaScript, HTML, and CSS.  
Core features include authentication via JWT and video delivery in **HLS format** with multiple resolutions.

---

## 🚀 Main Features

- **JWT Authentication**: Login & session handling with JSON Web Tokens  
- **Video streaming in HLS format** (`.m3u8`)  
- **Three selectable resolutions**:  
  - 480p (SD)  
  - 720p (HD)  
  - 1080p (Full HD)  
- **Email-based registration** with activation link  
- **Automatic background tasks** (ffmpeg transcoding, thumbnail creation) via Redis & RQ  

---

## 📦 Tech Stack

- **Backend**: Django, Django REST Framework, Gunicorn  
- **Auth**: JWT (via `djangorestframework-simplejwt`)  
- **DB**: PostgreSQL  
- **Queue**: Redis + RQ Worker  
- **Video Processing**: ffmpeg → HLS (480p, 720p, 1080p)  
- **Frontend**: Vanilla JavaScript, HTML, CSS  
- **Containerisierung**: Docker Compose  

---

## ⚙️ Quickstart

1) Repository klonen:
```bash
git clone <repo-url>
cd videoflix
```

2) Configure `.env`:
```bash
cp .env.template .env
# Fill in values for DB, Redis, Email, etc.
```

3) Starten:
```bash
docker-compose up --build
```
- Backend API: `http://localhost:8000`  
- Frontend (Static Server): `http://localhost:4200`  

---

## 🔑 Important Environment Variables (`.env`)

| Variable               | Description              | Example                  |
|------------------------|---------------------------|---------------------------|
| `SECRET_KEY`           | Django secret key         | `change-me-very-secret`   |
| `DEBUG`                | True/False                | `True`                    |
| `ALLOWED_HOSTS`        | Allowed hosts            | `localhost,127.0.0.1`     |
| `CSRF_TRUSTED_ORIGINS` | CSRF whitelist            | `http://localhost:4200`   |
| `DB_*`                 | Database credentials           | `videoflix / ********`    |
| `REDIS_HOST`           | Redis Host                | `redis`                   |
| `EMAIL_*`              | SMTP settings        | `smtp.example.com`        |
| `DJANGO_SUPERUSER_*`   | Auto superuser at startup | `admin / admin@example.com` |

---

## 🛠️ Useful Commands

Container öffnen:
```bash
docker-compose exec backend sh
```

Migrationen:
```bash
docker-compose exec backend python manage.py migrate
```

Superuser manuell:
```bash
docker-compose exec backend python manage.py createsuperuser
```

Logs:
```bash
docker-compose logs -f backend
```

---


---

## ✅ Tests

The backend comes with **pytest tests**.  
They cover authentication, video endpoints, and background tasks.

### Run tests locally

Open a container:
```bash
docker-compose exec backend sh
```

Run all tests:
```bash
pytest
```

With detailed output:
```bash
pytest -v
```

With coverage report:
```bash
pytest --cov
```


## 🔒 Security

- In production set `DEBUG=False`  
- Use strong passwords & secrets  
- Configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` correctly  
- Use HTTPS termination via Nginx/Proxy  
- Persistent volumes for `media/` and `static/`  
