class CanonicalDataError(RuntimeError):
    pass


class ValidationBlockedError(CanonicalDataError):
    pass


class RevisionConflictError(CanonicalDataError):
    pass


class ReleasePlanError(CanonicalDataError):
    pass
