"""
content/views.py
"""

from django.http import HttpRequest
from django.shortcuts import render


def main_view(request: HttpRequest):
    return render(request, "index.html")
