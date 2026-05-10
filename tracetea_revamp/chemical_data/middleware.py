from django.contrib import messages
from django.shortcuts import redirect
from rest_framework.exceptions import APIException

class GlobalAPIExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except APIException as e:
            # Handle APIException globally
            messages.error(request, str(e))
            # Redirect back to the same page (or a safe fallback)
            return redirect(request.META.get("HTTP_REFERER", "/"))
