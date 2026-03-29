from django.shortcuts import render
from django.http import HttpResponse
from django.views import View

def hello_world(request):
    context = {
        'title': 'Hello World',
        'message': 'Welcome to Django'
    }
    return render(request, 'hello.html', context)

class HelloView(View):
    def get(self, request):
        context = {'title': 'Hello View'}
        return render(request, 'hello.html', context)