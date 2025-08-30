# 🎬 Videoflix – Streaming-Plattform

Videoflix ist eine Streaming-Webapp mit einem Django-Backend und einem einfachen Frontend auf Basis von JavaScript, HTML und CSS.  
Im Zentrum stehen die Authentifizierung via JWT und die Auslieferung von Videos im **HLS-Format** in mehreren Auflösungen.

---

## 🚀 Haupt-Features

- **JWT-Authentifizierung**: Login & Session-Handling über JSON Web Tokens  
- **Videostreaming im HLS-Format** (`.m3u8`)  
- **Drei auswählbare Auflösungen**:  
  - 480p (SD)  
  - 720p (HD)  
  - 1080p (Full HD)  
- **E-Mail-gestützte Registrierung** mit Aktivierungslink  
- **Automatische Hintergrundprozesse** (ffmpeg-Transcoding, Thumbnail-Erstellung) über Redis & RQ  

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

2) `.env` konfigurieren:
```bash
cp .env.template .env
# Werte wie DB, Redis, E-Mail eintragen
```

3) Starten:
```bash
docker-compose up --build
```
- Backend API: `http://localhost:8000`  
- Frontend (Static Server): `http://localhost:4200`  

---

## 🔑 Wichtige Umgebungsvariablen (`.env`)

| Variable               | Beschreibung              | Beispiel                  |
|------------------------|---------------------------|---------------------------|
| `SECRET_KEY`           | Django Secret Key         | `change-me-very-secret`   |
| `DEBUG`                | True/False                | `True`                    |
| `ALLOWED_HOSTS`        | Erlaubte Hosts            | `localhost,127.0.0.1`     |
| `CSRF_TRUSTED_ORIGINS` | CSRF-Whitelist            | `http://localhost:4200`   |
| `DB_*`                 | DB-Zugangsdaten           | `videoflix / ********`    |
| `REDIS_HOST`           | Redis Host                | `redis`                   |
| `EMAIL_*`              | SMTP Einstellungen        | `smtp.example.com`        |
| `DJANGO_SUPERUSER_*`   | Auto-Superuser beim Start | `admin / admin@example.com` |

---

## 🛠️ Nützliche Befehle

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

## 🔒 Sicherheit

- In Produktion `DEBUG=False`  
- Sichere Passwörter & Secrets verwenden  
- `ALLOWED_HOSTS` und `CSRF_TRUSTED_ORIGINS` korrekt pflegen  
- HTTPS über Nginx/Proxy terminieren  
- Persistent Volumes für `media/` und `static/`  
