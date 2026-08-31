import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def hello(request):
    status = request.GET.get("status", "success")

    if status == "success":
        return JsonResponse({
            "success": True,
            "message": "Request processed successfully",
        }, status=200)

    if status == "bad":
        return JsonResponse({
            "success": False,
            "message": "Bad request",
        }, status=400)

    if status == "error":
        return JsonResponse({
            "success": False,
            "message": "Internal server error",
        }, status=500)

    return JsonResponse({
        "success": False,
        "message": "Unknown status",
    }, status=400)


@csrf_exempt
def echo(request):
    print("========== REQUEST ==========")

    print("Method:", request.method)
    print("Path:", request.path)
    print("Headers:", request.headers)
    print("Raw body:", request.body)

    print("=============================")

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid JSON",
            },
            status=400,
        )

    return JsonResponse({
        "success": True,
        "received": data,
    })
