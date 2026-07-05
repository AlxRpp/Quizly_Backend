import whisper
import yt_dlp
import json
import tempfile
import os
import shutil
from google import genai
from urllib.parse import urlparse, parse_qs
from ..models import Quiz, Question


class InvalidYouTubeURLError(Exception):
    """Custom error, get raised when the given url is not a valid youtube link.
    We use our own exception here instead of a generic one, so the serializer
    can catch exactly this and nothing else (dont wanna hide other bugs)."""
    pass


def extract_youtube_id(url: str):
    """Get the video id out of a youtube url. Works for the two common formats:
    youtu.be/ID and youtube.com/watch?v=ID (also with extra query params like
    timestamps). If none of the two match we raise InvalidYouTubeURLError.
    We use urlparse instead of regex, its already splitting the url in clean
    parts for us (netloc, path, query), way easier than doing it by hand."""
    parsed = urlparse(url)
    if "youtu.be" in parsed.netloc:
        video_id = parsed.path.lstrip("/")
    elif "youtube.com" in parsed.netloc:
        video_id = parse_qs(parsed.query).get("v", [None])[0]
    else:
        video_id = None

    if not video_id:
        raise InvalidYouTubeURLError()
    return video_id


def build_canonical_url(video_id):
    """Build back a clean, always-same youtube url from just the id. We need
    this because the client can send us many different youtube url formats,
    but in the db we always wanna save the SAME format (watch?v=ID)."""
    return f"https://www.youtube.com/watch?v={video_id}"


def download_audio(video_url):
    """Download only the audio (not the whole video) from a youtube link with
    yt-dlp, into a fresh temp folder. Important: we use tempfile.mkdtemp() and
    NOT TemporaryDirectory() as a with-block, because that would delete the
    file again before whisper even had the chance to read it! Gives back the
    real file path afterwards, cause we dont know the extension before yt-dlp
    decided it (m4a/webm/whatever)."""
    tmp_dir = tempfile.mkdtemp()
    outtmpl = os.path.join(tmp_dir, "audio.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "quiet": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        return ydl.prepare_filename(info)


def get_transcript(file_path):
    """Take a local audio file and let whisper turn it into text. Model size
    is "tiny" right now for fast testing, can be switched to "base"/"small"
    later for better accuracy (costs more time then, tiny is fastest)."""
    model = whisper.load_model("tiny")
    result = model.transcribe(file_path)
    return (result["text"])


def get_questions(transcript):
    """Send the transcript to gemini with a fixed prompt, so it gives back
    exactly the quiz-json we need (title, description, 10 questions with 4
    options each). Returns the RAW text from gemini, json.loads() still has
    to happen somewhere after this (currently done in build_quiz_from_url)."""
    prompt = """
        Based on the following transcript, generate a quiz in valid JSON format.
        The quiz must follow this exact structure:
        {{
        "title": "Create a concise quiz title based on the topic of the transcript.",
        "description": "Summarize the transcript in no more than 150 characters. Do not include any quiz questions or answers.",
        "questions": [
            {{
            "question_title": "The question goes here.",
            "question_options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "The correct answer from the above options"
            }},
            ...
            (exactly 10 questions)
        ]
        }}
        Requirements:
        - Each question must have exactly 4 distinct answer options.
        - Only one correct answer is allowed per question, and it must be present in 'question_options'.
        - The output must be valid JSON and parsable as-is (e.g., using Python's json.loads).
        - Do not include explanations, comments, or any text outside the JSON."""

    client = genai.Client()
    interaction = client.interactions.create(
        model="gemini-3.5-flash",
        input=prompt + transcript

    )
    return (interaction.output_text)


def create_quiz(user, canonical_url, quiz_data):
    """Small helper, only saves the Quiz row in db (title/description come
    from gemini, video_url from our own canonical url, owner from the
    currently logged in user)."""
    return Quiz.objects.create(
        owner=user,
        title=quiz_data["title"],
        description=quiz_data["description"],
        video_url=canonical_url,
    )


def create_questions(quiz, questions_data):
    """Saves all 10 Question rows for one quiz, one Question.objects.create()
    call per question from the gemini answer."""
    for q in questions_data:
        Question.objects.create(
            quiz=quiz,
            question_title=q["question_title"],
            question_options=q["question_options"],
            answer=q["answer"],
        )


def build_quiz_from_url(canonical_url, user):
    """This is the main pipeline the view calls: download audio -> transcribe
    -> ask gemini -> save everything in db. The temp folder from
    download_audio always gets deleted in the finally-block, even if
    something above crashes (whisper error, gemini error, invalid json,
    whatever) - so we never leave audio files laying around on the server."""
    tmp_dir = None
    try:
        audio_path = download_audio(canonical_url)
        tmp_dir = os.path.dirname(audio_path)
        transcript = get_transcript(audio_path)
        quiz_data = json.loads(get_questions(transcript))
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    quiz = create_quiz(user, canonical_url, quiz_data)
    create_questions(quiz, quiz_data["questions"])
    return quiz
