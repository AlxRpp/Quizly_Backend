from rest_framework import serializers
from ..models import Question, Quiz
from .utils import extract_youtube_id, build_canonical_url, InvalidYouTubeURLError


class QuestionSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
    updated_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")

    class Meta:
        model = Question
        fields = ['id', 'question_title',
                  'question_options', 'answer', 'created_at', 'updated_at']


class QuizSerializer(serializers.ModelSerializer):
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
    url = serializers.URLField()

    def validate_url(self, value):
        try:
            video_id = extract_youtube_id(value)
        except InvalidYouTubeURLError:
            raise serializers.ValidationError("Unvalid YouTube_URL")
        return build_canonical_url(video_id)
