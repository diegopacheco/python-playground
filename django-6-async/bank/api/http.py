import json
from functools import wraps

from django.http import JsonResponse

from ..domain.errors import BankError, ValidationError


def json_response(payload, status=200):
    return JsonResponse(payload, status=status, json_dumps_params={"indent": 2})


def read_body(request):
    if not request.body:
        return {}
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        raise ValidationError("request body is not valid JSON")
    if not isinstance(body, dict):
        raise ValidationError("request body must be a JSON object")
    return body


def require(body, *fields):
    missing = [field for field in fields if body.get(field) in (None, "")]
    if missing:
        raise ValidationError(f"missing required fields: {', '.join(missing)}")
    return [body[field] for field in fields]


def endpoint(*methods):
    def decorator(view):
        @wraps(view)
        async def wrapper(request, *args, **kwargs):
            if request.method not in methods:
                return json_response(
                    {"error": f"{request.method} not allowed"}, status=405
                )
            try:
                return await view(request, *args, **kwargs)
            except BankError as error:
                return json_response({"error": str(error)}, status=error.status)

        return wrapper

    return decorator
