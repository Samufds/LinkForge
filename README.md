# ⬡ LinkForge

A **URL Shortener + YouTube Downloader** built with:

- **FastAPI** — async Python web framework
- **PostgreSQL** — [Neon.tech](https://neon.tech)
- **SQLAlchemy 2.0** — async-compatible ORM
- **Pydantic v2** — request/response validation
- **yt-dlp** — YouTube video & audio downloads

**Note: The downloader uses browser cookie authentication which works well when you run it on your own machine.**


### 1. Clone & install

```bash
git clone <your-repo>
cd url-shortener
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set up your database

**PostgreSQL for Database**
- [neon.tech](https://neon.tech)

Copy your connection string it will look like this: (`postgresql://user:pass@host/dbname`)

### 3. Configure environment

```bash
cp .env.example .env
```

### 4. Run

```bash
bash run.sh
# or directly:
uvicorn app.main:app --reload
```

Open **http://localhost:8000** — tables are created automatically on first run.

---

**Create URL — example request:**
```json
POST /api/urls/
{
  "original_url": "https://example.com/very/long/path",
  "custom_alias": "my-link"   // optional
}
```



