"""Consistent JSON error envelopes for the PageBack API."""

from rest_framework.views import exception_handler


def pageback_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    message = response.data
    if isinstance(message, dict) and "detail" in message:
        message = str(message["detail"])
    elif not isinstance(message, str):
        message = "Request could not be completed."

    response.data = {
        "success": False,
        "error": {
            "code": "REQUEST_ERROR",
            "message": message,
        },
    }
    return response
