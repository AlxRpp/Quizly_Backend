import whisper
import yt_dlp
import json
import tempfile
import os
from google import genai
from urllib.parse import urlparse, parse_qs


class InvalidYouTubeURLError(Exception):
    pass


def extract_youtube_id(url: str):
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
    return f"https://www.youtube.com/watch?v={video_id}"


def download_audio(video_url):
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
    model = whisper.load_model("tiny")
    result = model.transcribe(file_path)
    return (result["text"])


def get_questions(transcript):
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
