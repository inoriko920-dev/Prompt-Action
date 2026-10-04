class CanonicalDataError(RuntimeError):
    pass


class ValidationBlockedError(CanonicalDataError):
    pass


class RevisionConflictError(CanonicalDataError):
    pass


class ReleasePlanError(CanonicalDataError):
    pass


class ReleaseWorkflowError(CanonicalDataError):
    """STEP 10 release failure with a stable machine-readable code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}
