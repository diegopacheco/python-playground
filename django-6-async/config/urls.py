from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

urlpatterns = [
    path("", include("bank.web.urls")),
    path("api/", include("bank.api.urls")),
] + staticfiles_urlpatterns()
