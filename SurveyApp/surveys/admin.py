from django.contrib import admin
from .models import Survey, Question, Choice, Answer

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3

class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    list_display = ('text', 'survey', 'type')
    list_filter = ('survey', 'type')

class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')

admin.site.register(Survey, SurveyAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer)
