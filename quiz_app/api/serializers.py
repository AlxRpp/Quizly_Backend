from rest_framework import serializers
from ..models import Question, Quiz
from .utils import extract_youtube_id, build_canonical_url, InvalidYouTubeURLError


class QuestionSerializer(serializers.ModelSerializer):
    """Serializes a Question; only used nested inside QuizSerializer."""
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
    updated_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")

    class Meta:
        model = Question
        fields = ['id', 'question_title',
                  'question_options', 'answer', 'created_at', 'updated_at']


class QuizSerializer(serializers.ModelSerializer):
    """Serializer for a quiz (list/detail/create/patch).

    created_at, updated_at and video_url are read_only; only title and
    description can be changed via patch.
    """
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
    """Validates that the client-supplied url is a YouTube url."""
    url = serializers.URLField()

    def validate_url(self, value):
        """Extract the video id and return its canonical YouTube url.

        Raises:
            ValidationError: if the url isn't a valid YouTube url.
        """
        try:
            video_id = extract_youtube_id(value)
        except InvalidYouTubeURLError:
            raise serializers.ValidationError("Unvalid YouTube_URL")
        return build_canonical_url(video_id)
