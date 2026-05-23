from typing import Any


def success_response(data: Any = None, message: str = "OK", code: str = "SUCCESS") -> dict[str, Any]:
    return {"code": code, "message": message, "data": data}


def error_response(message: str, code: str = "ERROR", detail: Any = None) -> dict[str, Any]:
    payload = {"code": code, "message": message, "data": None}
    if detail is not None:
        payload["detail"] = detail
    return payload
