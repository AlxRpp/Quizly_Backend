from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import QuizSerializer, ValidateInputURLSerializer
from .permissions import IsOwner
from .utils import download_audio, get_transcript, get_questions
from ..models import Quiz, Question
import os
import json
import shutil


class ListOrCreateQuizView(ListCreateAPIView):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(owner=self.request.user)

    def post(self, request, *args, **kwargs):
        input_serializer = ValidateInputURLSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        cannonical_url = input_serializer.validated_data["url"]

        tmp_dir = None
        try:
            audio_path = download_audio(cannonical_url)
            tmp_dir = os.path.dirname(audio_path)
            transcript = get_transcript(audio_path)
            quiz_data = json.loads(get_questions(transcript))
        except Exception:
            return Response({"error": "something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            if tmp_dir:
                shutil.rmtree(tmp_dir, ignore_errors=True)

        quiz = Quiz.objects.create(
            owner=request.user,
            title=quiz_data["title"],
            description=quiz_data["description"],
            video_url=cannonical_url
        )
        for q in quiz_data["questions"]:
            Question.objects.create(
                quiz=quiz,
                question_title=q["question_title"],
                question_options=q["question_options"],
                answer=q['answer']
            )
        return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)


class QuizDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated, IsOwner]
