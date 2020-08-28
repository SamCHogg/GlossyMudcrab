class AlreadySignedUpException(Exception):
    role: str

    def __init__(self, message, role):
        self.role = role
        super().__init__(message)


class RosterFullException(Exception):
    pass


class EventNotFoundException(Exception):
    pass
