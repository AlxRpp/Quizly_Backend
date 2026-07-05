from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


class Quiz(models.Model):
    """One quiz that got generated from a youtube video, belongs to exactly
    one user (owner)."""
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="quiz_owner")
    title = models.CharField(blank=False, null=False, max_length=255)
    description = models.TextField(null=False, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    video_url = models.URLField(null=False, blank=False, max_length=200)

    class Meta:
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'
        ordering = ['id']

    def __str__(self):
        return f"{self.title} | {self.created_at}"


class Question(models.Model):
    """One single question that belongs to a quiz, with 4 answer options and
    the correct answer."""
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name='questions')
    question_title = models.CharField(blank=False, null=False, max_length=250)
    question_options = models.JSONField(default=list)
    answer = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['id']

    def __str__(self):
        return f"{self.question_title}"
