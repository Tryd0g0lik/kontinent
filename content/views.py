from django.http import HttpRequest
from django.shortcuts import render

# Create your views here.

def main_view(request: HttpRequest):
    return render(request, "index.html")