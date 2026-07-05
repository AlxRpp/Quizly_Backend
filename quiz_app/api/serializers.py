from rest_framework import serializers
from ..models import Question, Quiz
from .utils import extract_youtube_id, build_canonical_url, InvalidYouTubeURLError


class QuestionSerializer(serializers.ModelSerializer):
    """Turns one Question object into json, only used nested inside
    QuizSerializer, never on its own right now."""
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
    updated_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")

    class Meta:
        model = Question
        fields = ['id', 'question_title',
                  'question_options', 'answer', 'created_at', 'updated_at']


class QuizSerializer(serializers.ModelSerializer):
    """Main serializer for a quiz. Used as output for list/detail/create and
    also as input for patch. created_at, updated_at and video_url are
    read_only so a client cant overwrite them - only title and description
    are meant to be changed via patch."""
    questions = QuestionSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%SZ", read_only=True)
    updated_at = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%SZ", read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description',
                  'created_at', 'updated_at', 'video_url', 'questions']
        read_only_fields = ['video_url']


class ValidateInputURLSerializer(serializers.Serializer):
    """Only used for the create-quiz request, checks that the url field the
    client sent is really a youtube url."""
    url = serializers.URLField()

    def validate_url(self, value):
        """Take the raw url from the client, extract the video id out of it
        and give back a clean canonical youtube url. If its not a youtube
        url at all, this raises ValidationError so DRF answers 400
        automatically, before we ever try to download anything."""
        try:
            video_id = extract_youtube_id(value)
        except InvalidYouTubeURLError:
            raise serializers.ValidationError("Unvalid YouTube_URL")
        return build_canonical_url(video_id)
