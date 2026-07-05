from django.urls import path
from .views import ListOrCreateQuizView, QuizDetailView

urlpatterns = [
    path('quizzes/', ListOrCreateQuizView.as_view(), name='quizzes'),
    path('quizzes/<int:pk>/', QuizDetailView.as_view(), name='quiz-detail')
]
