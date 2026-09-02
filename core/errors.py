class EdithError(Exception):
    def __init__(self, user_message: str, detail: str = "", error_type: str = "internal_error"):
        self.user_message = user_message
        self.detail = detail
        self.error_type = error_type
        super().__init__(user_message)


class ServiceDownError(EdithError):
    def __init__(self, service_name: str, detail: str = ""):
        super().__init__(
            user_message=f"Can't reach {service_name} right now.",
            detail=detail or f"{service_name} did not respond.",
            error_type="service_down",
        )


class InvalidInputError(EdithError):
    def __init__(self, user_message: str, detail: str = ""):
        super().__init__(user_message, detail, error_type="invalid_input")


class InternalError(EdithError):
    def __init__(self, detail: str = ""):
        super().__init__(
            user_message="Something went wrong on my end.",
            detail=detail,
            error_type="internal_error",
        )