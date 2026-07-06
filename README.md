# Quizly Backend

Django REST Framework backend for **Quizly** — turn any YouTube video into a 10-question multiple-choice quiz. Paste a YouTube link, and the backend downloads the audio, transcribes it with Whisper, and generates the quiz with Google's Gemini Flash API.

## Requirements

- Python **3.12 or higher**
- [FFmpeg](https://ffmpeg.org/) installed **globally** on your system (required by Whisper and yt-dlp for audio extraction)
- A free Gemini API key (see below)

## Setup

1. Clone the repository and create a virtual environment:
   ```bash
   python3.12 -m venv env
   source env/bin/activate   # Windows: env\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Make sure FFmpeg is installed and available on your `PATH`:
   ```bash
   ffmpeg -version
   ```
   - macOS: `brew install ffmpeg`
   - Ubuntu/Debian: `sudo apt install ffmpeg`
   - Windows: download from [ffmpeg.org](https://ffmpeg.org/download.html) and add it to your `PATH`

4. Create your `.env` file from the template:
   ```bash
   cp .env.example .env
   ```

5. Get a free Gemini API key:
   - Go to [Google AI Studio](https://aistudio.google.com/apikey)
   - Sign in with a Google account
   - Click "Create API key" and copy it
   - Paste it into `.env`:
     ```
     GEMINI_API_KEY=your-key-here
     ```

6. Apply database migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Frontend / CORS Setup

The frontend and this backend run as two separate applications, usually on different ports (e.g. VS Code Live Server on `:5500`, Angular on `:4200`, React on `:3000`, Vite on `:5173`). Because of that, the backend must explicitly allow the frontend's origin — otherwise the browser blocks every request, even though the API itself works fine (this is a browser security rule called the [Same-Origin Policy](https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy), not a bug in the backend).

If you are testing this project with your own frontend, update these three values in your `.env` to match wherever **you** run it:
```
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5500
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:5500
```
- `CORS_ALLOWED_ORIGINS`: the exact origin (protocol + host + port) your frontend is served from. Multiple origins can be comma-separated, e.g. `http://127.0.0.1:5500,http://localhost:4200`.
- `ALLOWED_HOSTS`: which hostnames Django itself accepts requests for.
- `CSRF_TRUSTED_ORIGINS`: same idea as CORS, for state-changing requests (POST/PATCH/DELETE).

Only the **port** usually needs to change (Live Server → `5500`, Angular → `4200`, React → `3000`, Vite → `5173`, ...) — just edit the value and restart the server, no code changes needed.

> **Important:** write these values as plain URLs, comma-separated if there are several. Do **not** wrap them in brackets or quotes like a JSON array (`["http://127.0.0.1:5500"]` is wrong) — just `http://127.0.0.1:5500`.

## Troubleshooting

- **`pip install` fails on `yt-dlp` with "No matching distribution found" / package-age warnings:** some pip security tooling blocks very recently published package versions. Try `pip install -U yt-dlp` on its own, or `pip install --pre "yt-dlp[default]"`.
- **CORS error in the browser console mentioning `credentials mode is 'include'`:** make sure `CORS_ALLOW_CREDENTIALS = True` is set in `core/settings.py` (already the case in this repo) — needed because the JWT cookies must be sent cross-origin.

## Authentication

Authentication uses JWT (access + refresh tokens) stored in **httpOnly cookies**, not returned in the response body. The frontend never handles raw tokens in JavaScript — the browser sends the cookies automatically with every request. On logout, the refresh token is blacklisted server-side and can never be reused.

## Main Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/register/` | Create a new account |
| POST | `/api/login/` | Log in, sets JWT cookies |
| POST | `/api/logout/` | Log out, blacklists the refresh token and clears cookies |
| POST | `/api/token/refresh/` | Get a new access token from the refresh cookie |
| POST | `/api/quizzes/` | Create a new quiz from a YouTube URL |
| GET | `/api/quizzes/` | List all quizzes of the logged-in user |
| GET / PATCH / DELETE | `/api/quizzes/<id>/` | Retrieve, update (title/description), or delete a single quiz |

## Admin Panel

Quizzes and questions can be managed directly at `/admin/`. Create a superuser first:
```bash
python manage.py createsuperuser
```
