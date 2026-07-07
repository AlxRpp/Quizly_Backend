from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import QuizSerializer, ValidateInputURLSerializer
from .permissions import IsOwner
from .utils import build_quiz_from_url
from ..models import Quiz


class ListOrCreateQuizView(ListCreateAPIView):
    """List the request user's quizzes, or create a new one from a YouTube url."""
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(owner=self.request.user)

    def post(self, request, *args, **kwargs):
        """Validate the url, then run utils.build_quiz_from_url
        (yt-dlp -> whisper -> Gemini -> save).

        Returns:
            201 with the created quiz on success.
            400 if the url isn't a valid YouTube url.
            500 if the download/transcription/generation pipeline fails.
        """
        input_serializer = ValidateInputURLSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        canonical_url = input_serializer.validated_data["url"]

        try:
            quiz = build_quiz_from_url(canonical_url, request.user)
        except Exception:
            return Response({"error": "something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)


class QuizDetailView(RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a single quiz by id.

    queryset is intentionally not filtered by owner, so a non-owner gets a
    403 (via IsOwner) instead of a 404.
    """
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated, IsOwner]
