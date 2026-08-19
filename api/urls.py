from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health(_request):
    return Response(
        {
            "success": True,
            "data": {"service": "PageBack", "status": "ok"},
            "message": "PageBack API is running.",
        }
    )


urlpatterns = [
    path("health/", health, name="api-health"),
]
