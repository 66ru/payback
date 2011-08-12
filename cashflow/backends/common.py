class SendPaymentFailureException(BaseException):
    def __init__(self, message):
        self._message = message

    def get_message(self):
        return self._message