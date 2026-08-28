from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
async def index(request):
    return render(request, "bank/index.html")
