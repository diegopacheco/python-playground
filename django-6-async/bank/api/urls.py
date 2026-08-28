from django.urls import path

from .views import accounts, profiles, transfers

urlpatterns = [
    path("profiles/", profiles.collection),
    path("profiles/<int:profile_id>/", profiles.detail),
    path("accounts/", accounts.collection),
    path("accounts/<int:account_id>/", accounts.detail),
    path("accounts/<int:account_id>/deposit/", accounts.deposit),
    path("accounts/<int:account_id>/withdraw/", accounts.withdraw),
    path("accounts/<int:account_id>/transactions/", accounts.statement),
    path("transfers/", transfers.create),
]
