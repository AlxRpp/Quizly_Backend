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
