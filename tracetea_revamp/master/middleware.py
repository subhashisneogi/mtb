from django.utils.timezone import now
from django.shortcuts import render

class Custom404Middleware:
    def __init__(self, get_response):   
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code == 404:
            return render(request, "404.html", status=404)
        
        return response
    

# class Custom500Middleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         try:
#             response = self.get_response(request)
#             return response
#         except Exception as e:
#             return render(request, "500.html", status=500)
       


class Custom500Middleware:
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            # Log the exception here if needed
            return self.handle_exception(request, e)

    def handle_exception(self, request, exception):
        return render(request, "500.html", status=500)