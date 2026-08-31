from django.http import JsonResponse


def hello(request):
    return JsonResponse({
        "message": "Hello from Webhook Sender!",
        "method": request.method,
        "path": request.path,
    })
