from django.urls import path

from novels import views as novel_views
from web import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("accounts/signup/", views.signup, name="signup"),
    path("demo/", views.demo, name="demo"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("novels/import/", novel_views.import_novel, name="import_novel"),
    path("novels/<int:novel_id>/", novel_views.novel_detail, name="novel_detail"),
]
