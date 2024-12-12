class RetryLimitExceededError(Exception):
    def __init__(self, error: str, message=None):
        if message is None:
            message = f"The retry limit has been reached.\n{error}"
        super().__init__(message)
