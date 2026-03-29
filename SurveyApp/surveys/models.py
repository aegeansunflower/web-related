from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Survey(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_surveys')
    requires_login = models.BooleanField(default=True, help_text="Checked = Account required. Unchecked = Open to everyone.")

    @property
    def total_responses(self):
        return Answer.objects.filter(question__survey=self).values('session_id').distinct().count()

    def __str__(self):
        return self.title

class Question(models.Model):
    RADIO = 'radio'
    CHECKBOX = 'checkbox'
    TEXT = 'text'
    
    QUESTION_TYPES = [
        (RADIO, 'Single Choice (Radio)'),
        (CHECKBOX, 'Multiple Choice (Checkbox)'),
        (TEXT, 'Text Input'),
    ]

    survey = models.ForeignKey(Survey, related_name='questions', on_delete=models.CASCADE)
    text = models.CharField(max_length=500)
    type = models.CharField(max_length=10, choices=QUESTION_TYPES, default=RADIO)
    required = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.survey.title} - {self.text}"

class Choice(models.Model):
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    text = models.CharField(max_length=200)

    def __str__(self):
        return self.text

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)
    text_answer = models.TextField(null=True, blank=True)
    session_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer to {self.question.text}"
