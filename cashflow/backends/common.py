class CashflowBaseException(BaseException):
    def __init__(self, message, *args, **kwargs):
        super(CashflowBaseException, self).__init__(*args, **kwargs)
        self._message = message

    def get_message(self):
        return self._message


class SendPaymentFailureException(CashflowBaseException):
    pass
