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
    """Raised when a given url is not a valid YouTube link."""
    pass


def extract_youtube_id(url: str):
    """Extract the video id from a youtu.be/ID or youtube.com/watch?v=ID url
    (including urls with extra query params, e.g. timestamps).

    Raises:
        InvalidYouTubeURLError: if the url matches neither format.
    """
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
    """Build the canonical https://www.youtube.com/watch?v=<id> url from a video id."""
    return f"https://www.youtube.com/watch?v={video_id}"


def download_audio(video_url):
    """Download only the audio track of a YouTube video into a fresh temp
    directory and return the resulting file path.

    Uses tempfile.mkdtemp() rather than TemporaryDirectory(): the latter
    would delete the directory before whisper gets a chance to read the file.
    """
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
    """Transcribe a local audio file to text via whisper.

    Uses the "tiny" model for speed; swap for "base"/"small" for higher
    accuracy at the cost of runtime.
    """
    model = whisper.load_model("tiny")
    result = model.transcribe(file_path)
    return (result["text"])


def get_questions(transcript):
    """Send the transcript to Gemini and return the raw quiz JSON text
    (title, description, 10 questions with 4 options each).

    Returns:
        str: raw text from Gemini, not yet parsed with json.loads().
    """
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
    """Create and save a Quiz row from Gemini's quiz_data, the canonical
    video url, and the owning user."""
    return Quiz.objects.create(
        owner=user,
        title=quiz_data["title"],
        description=quiz_data["description"],
        video_url=canonical_url,
    )


def create_questions(quiz, questions_data):
    """Create and save one Question row per entry in questions_data."""
    for q in questions_data:
        Question.objects.create(
            quiz=quiz,
            question_title=q["question_title"],
            question_options=q["question_options"],
            answer=q["answer"],
        )


def build_quiz_from_url(canonical_url, user):
    """Run the full pipeline: download audio, transcribe, generate questions
    via Gemini, then save the quiz and its questions.

    The temp audio directory is always removed afterwards, even if a step
    raises (whisper/Gemini/JSON errors).

    Returns:
        Quiz: the newly created quiz instance.
    """
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
