"""
content/views.py
"""

from django.http import HttpRequest
from django.shortcuts import render

from content.file_validator import FileDuplicateChecker

fduplicate = FileDuplicateChecker()


def main_view(request: HttpRequest):
    return render(request, "index.html")
