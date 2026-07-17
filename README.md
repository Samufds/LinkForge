# LinkForge

LinkForge is a full stack web application with a URL shortener that generates short trackable links with custom aliases and a YouTube downloader.

## Features

- Shorten any URL to a clean short link
- Custom aliases (e.g. /my-link)
- Click tracking on every visit shows the number of times you've visited the video.
- Download as MP4 video or MP3 audio
- Quality selection — Best, 720p, 480p, 360p

## Tech Stack
- HTML, CSS, JavaScript
- PostgreSQL (hosted on Neon.tech)
- FastAPI, Python, SQLAlchemy, Pydantic v2, yt-dlp, Uvicorn

**Note: The downloader uses browser cookie authentication which works well when you run it on your own machine.**


## 1. Clone & install

```bash
git clone <your-repo>
cd url-shortener
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## 2. Set up your database

**PostgreSQL for Database**
- [neon.tech](https://neon.tech)

Copy your connection string that will look like this: (`postgresql://user:pass@host/dbname`)

### 3. Configure environment

```bash
cp .env.example .env
```

## Preview
![image alt](LinkForge.png)
![image alt](history.png)


