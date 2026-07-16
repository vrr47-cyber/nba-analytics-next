from fastapi import Request

from backend.app.services.application import AppServices


def get_services(request: Request) -> AppServices:
    return request.app.state.services
