from django.urls import path

from novels import views as novel_views
from web import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("accounts/signup/", views.signup, name="signup"),
    path("demo/", views.demo, name="demo"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("library/collections/create/", views.create_collection, name="create_collection"),
    path("library/collections/<int:collection_id>/", views.collection_detail, name="collection_detail"),
    path("novels/<int:novel_id>/library-action/", views.library_action, name="library_action"),
    path("novels/import/", novel_views.import_novel, name="import_novel"),
    path("novels/<int:novel_id>/", novel_views.novel_detail, name="novel_detail"),
]
