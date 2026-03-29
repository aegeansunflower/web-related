from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Survey, Question, Choice, Answer, UserProfile
from django.db.models import Count
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required

def survey_list(request):
    surveys = Survey.objects.all().order_by('-created_at')
    return render(request, 'surveys/survey_list.html', {'surveys': surveys})

def survey_detail(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    
    if survey.requires_login and not request.user.is_authenticated:
        messages.error(request, "You must be logged in to take this survey.")
        return redirect('login')

    session_id = request.session.session_key
    if not session_id:
        request.session.create()
        session_id = request.session.session_key
        
    user = request.user if request.user.is_authenticated else None
    
    # Check if user already took this survey
    already_taken = False
    if user:
        already_taken = Answer.objects.filter(question__survey=survey, user=user).exists()
    else:
        already_taken = Answer.objects.filter(question__survey=survey, session_id=session_id).exists()
        
    if request.method == 'POST':
        if already_taken:
            messages.error(request, "You have already completed this survey.")
            return redirect('survey_results', survey_id=survey.id)
            
            
        for question in survey.questions.all():
            if question.type == Question.TEXT:
                answer_text = request.POST.get(f'question_{question.id}')
                if answer_text:
                    Answer.objects.create(question=question, text_answer=answer_text, session_id=session_id, user=user)
            elif question.type == Question.RADIO:
                choice_id = request.POST.get(f'question_{question.id}')
                if choice_id:
                    choice = get_object_or_404(Choice, pk=choice_id)
                    Answer.objects.create(question=question, choice=choice, session_id=session_id, user=user)
            elif question.type == Question.CHECKBOX:
                choice_ids = request.POST.getlist(f'question_{question.id}')
                for cid in choice_ids:
                    choice = get_object_or_404(Choice, pk=cid)
                    Answer.objects.create(question=question, choice=choice, session_id=session_id, user=user)
        
        # Award points
        if user:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.points += 10
            profile.save()
            messages.success(request, "Thanks for completing the survey! You earned 10 points.")
        else:
            messages.success(request, "Thanks for completing the survey!")
            
        return redirect('survey_results', survey_id=survey.id)
    
    if already_taken:
        messages.info(request, "You have already completed this survey. Here are the results.")
        return redirect('survey_results', survey_id=survey.id)
        
    import json
    survey_data = {
        'id': survey.id,
        'title': survey.title,
        'description': survey.description,
        'questions': []
    }
    for q in survey.questions.all():
        survey_data['questions'].append({
            'id': q.id,
            'text': q.text,
            'type': q.type,
            'required': q.required,
            'choices': [{'id': c.id, 'text': c.text} for c in q.choices.all()]
        })
    survey_data_json = json.dumps(survey_data)
        
    return render(request, 'surveys/survey_detail.html', {'survey': survey, 'survey_data_json': survey_data_json})

def survey_results(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    results = []
    for question in survey.questions.all():
        if question.type in [Question.RADIO, Question.CHECKBOX]:
            choices = question.choices.annotate(num_answers=Count('answer')).order_by('-num_answers')
            results.append({
                'question': question,
                'choices': choices
            })
        else:
            answers = Answer.objects.filter(question=question).exclude(text_answer__isnull=True).exclude(text_answer='')
            results.append({
                'question': question,
                'answers': answers
            })
            
    return render(request, 'surveys/survey_results.html', {'survey': survey, 'results': results})

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('survey_list')
    else:
        form = UserCreationForm()
    return render(request, 'surveys/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('survey_list')
    else:
        form = AuthenticationForm()
    return render(request, 'surveys/login.html', {'form': form})



@login_required
def survey_create(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    is_admin = request.user.is_superuser

    if not is_admin and profile.points < 50:
        messages.error(request, f"You need at least 50 points to create a survey. You currently have {profile.points} points.")
        return redirect('survey_list')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        requires_login = request.POST.get('requires_login') == 'on'
        
        survey = Survey.objects.create(
            title=title, 
            description=description, 
            creator=request.user, 
            requires_login=requires_login
        )
        
        if not is_admin:
            profile.points -= 50
            profile.save()
            messages.success(request, "Survey created! You spent 50 points. Now add questions to it.")
        else:
            messages.success(request, "Survey created! As an admin, you triggered this for free. Now add questions to it.")
            
        return redirect('survey_list')

    return render(request, 'surveys/survey_create.html', {
        'points': profile.points, 
        'is_admin': is_admin
    })

def logout_view(request):
    if request.method == 'POST':
        auth_logout(request)
        return redirect('survey_list')
    return render(request, 'surveys/logout.html')

@login_required
def profile_view(request):
    # Get answers made by this user
    user_answers = Answer.objects.filter(user=request.user).select_related('question__survey', 'choice')
    
    # Let's group answers by survey
    surveys_taken = {}
    for answer in user_answers:
        survey = answer.question.survey
        if survey not in surveys_taken:
            surveys_taken[survey] = []
        surveys_taken[survey].append(answer)
        
    return render(request, 'surveys/profile.html', {'surveys_taken': surveys_taken})
