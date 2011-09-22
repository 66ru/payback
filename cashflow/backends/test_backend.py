#-*- coding: UTF-8 -*-
from payback.cashflow.backends.common import RedirectNeededException

def send_payment(payment):
    raise RedirectNeededException('http://example.com/', message='wow!')

def success(request):
    return True

def fail(request):
    return True
