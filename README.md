# Hidden Gems

A community-driven platform for discovering and sharing indie games. Hidden Gems connects independent developers with players by providing a space to upload, browse, and explore games that might otherwise go unnoticed.

---

# Production Link

[hiddengems](http://hiddengems.me)

---

## Pitch

Indie games are some of the most creative and innovative experiences in gaming, yet they often struggle to reach an audience. Hidden Gems solves this by giving developers a straightforward publishing pipeline and giving players a curated place to find their next favorite title.

---

## Key Features

- **Browse Games** — Explore a catalog of indie titles sorted by newest releases
- **Game Pages with Steam Integration** — View descriptions, screenshots, genre, pricing, and developer info, linked to the associated steam storefront page
- **AI-Powered Search** — Natural language game search powered by OpenAI; describe a vibe, genre, or mood and get relevant results (e.g. "something relaxing" or "free horror games")
- **Developer Uploads** — Authenticated developers can publish games with metadata, thumbnails, and build files
- **Browser-Playable Demos** — As availble, some games have browser playable demos
- **User Authentication** — Secure sign-up, login, and session management
- **Admin Panel** — Manage games, users, and platform content

---

### Development Prerequisites

- Python 3.10+
- PostgreSQL (production) or SQLite (development)
- Docker & Docker Compose (optional, used for CD)

### Local Setup

```bash
git clone https://github.com/CS4300-CS5300-SP26/hiddengems.git
cd hiddengems
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your values
python manage.py migrate
python manage.py runserver
```

### Docker

```bash
docker compose up --build
```

The app will be available at `http://localhost:8000`.

### Running Tests

```bash
python manage.py test
```

---

## Architecture & Frameworks

| Layer | Technology |
|---|---|
| Web Framework | Django 4.2 |
| Database | PostgreSQL (prod) / SQLite (dev) |
| Static Files | WhiteNoise |
| Application Server | Gunicorn |
| Containerization | Docker / Docker Compose |
| Config Management | python-dotenv |
| Testing | Django TestCase, Behave (BDD), Coverage |
| AI Integration | OpenAI SDK |

The project follows a standard Django MTV (Model–Template–View) architecture. Environment-based configuration via `DEVELOPMENT_MODE` switches the database backend automatically between SQLite (local) and PostgreSQL (production/CI).

---

## Authors

| Name | GitHub |
|---|---|
| Devin Haggitt | [@dhaggitt](https://github.com/dhaggitt) |
| Evan Futey | [@efutey15](https://github.com/efutey15) |
| Isaiah Douglas (Allo-DinoMage) | [@Allo-DinoMage](https://github.com/Allo-DinoMage) |
| Bryson Curtis | [@ThePieBaker90](https://github.com/ThePieBaker90) |
| Jayden Royer | [@Royer5000](https://github.com/Royer5000) |