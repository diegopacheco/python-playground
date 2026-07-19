import sys

from django.conf import settings
from django.core.management import execute_from_command_line
from django.http import JsonResponse
from django.urls import path

settings.configure(
    DEBUG=True,
    SECRET_KEY="python-essentials-django-key",
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["*"],
    MIDDLEWARE=["django.middleware.common.CommonMiddleware"],
)

tasks = [
    {"id": 1, "title": "learn django", "done": False},
    {"id": 2, "title": "ship poc", "done": True},
]


def home(request):
    return JsonResponse({"service": "python-essentials-django", "status": "ok"})


def list_tasks(request):
    return JsonResponse({"tasks": tasks})


def task_detail(request, task_id):
    found = next((t for t in tasks if t["id"] == task_id), None)
    if found is None:
        return JsonResponse({"error": "not found"}, status=404)
    return JsonResponse(found)


urlpatterns = [
    path("", home),
    path("tasks/", list_tasks),
    path("tasks/<int:task_id>/", task_detail),
]


if __name__ == "__main__":
    execute_from_command_line([sys.argv[0], "runserver", "8000"])
