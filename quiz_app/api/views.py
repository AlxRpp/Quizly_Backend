from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import QuizSerializer, ValidateInputURLSerializer
from .permissions import IsOwner
from .utils import build_quiz_from_url
from ..models import Quiz


class ListOrCreateQuizView(ListCreateAPIView):
    """GET gives back all quizzes from the logged in user, POST creates a new
    one from a youtube url (download audio, transcribe, let gemini build the
    questions)."""
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Only show quizzes that belong to the request user, not every
        quiz in the whole db."""
        return Quiz.objects.filter(owner=self.request.user)

    def post(self, request, *args, **kwargs):
        """Validate the url, then let utils.build_quiz_from_url do the heavy
        work (yt-dlp, whisper, gemini). If something breaks in that
        pipeline we just answer 500, its not really the users fault, more
        like our external services."""
        input_serializer = ValidateInputURLSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        canonical_url = input_serializer.validated_data["url"]

        try:
            quiz = build_quiz_from_url(canonical_url, request.user)
        except Exception:
            return Response({"error": "something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)


class QuizDetailView(RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE for one single quiz by id. queryset is NOT filtered
    by owner on purpose, cause we want a real 403 when its not your quiz
    (not just a 404) - the actual check for that happens in IsOwner."""
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated, IsOwner]
