#-*- coding: UTF-8 -*-
from hashlib import md5
from ConfigParser import NoOptionError, NoSectionError
from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from payback.cashflow.backends.common import RedirectNeededException
from payback.cashflow.models import Payment, ClientBackend

###
# config:
#
# [auth]
# login = login
# pass1 = someting1
# pass2 = someting2
#
# [dev]
# debug = true # необязательно


def sign(*args):
    param_str = ":".join([str(a) for a in args])
    return md5(param_str).hexdigest()

def send_payment(payment): # throws SendPaymentFailureException
    client_backend = ClientBackend.objects.get(client=payment.client, backend=payment.backend)
    cp = client_backend.get_config_parser()

    login = cp.get('auth', 'login')
    pwd = cp.get('auth', 'pass1')

    debug = False
    try:
        debug = cp.getboolean('dev', 'debug')
    except (NoOptionError, NoSectionError):
        pass


    if not debug:
        url = "https://merchant.roboxchange.com/Index.aspx"
    else:
        url = "http://test.robokassa.ru/Index.aspx"

    url += \
          ("?MrchLogin=%s" % login) + \
          ("&OutSum=%s" % payment.amount) + \
          ("&InvId=%s" % payment.id) + \
          ("&Desc=%s" % payment.comment) + \
          ("&SignatureValue=%s" % sign(login, payment.amount, payment.id, pwd))

    raise RedirectNeededException(url, '(send payment): %s' % url)


class ResultForm(forms.Form):
    OutSum = forms.DecimalField(min_value=0)
    InvId = forms.IntegerField(min_value=1)
    SignatureValue = forms.CharField(max_length=32)

class FormOkException(BaseException):
    def __init__(self, payment, *args, **kwargs):
        super(FormOkException, self).__init__(*args, **kwargs)
        self.payment = payment

def _success_fail_request_helper(request):
    form = ResultForm(request.POST)
    if form.is_valid():
        payment_id = form.cleaned_data['InvId']
        try:
            p = Payment.objects.get(pk=payment_id)
        except Payment.DoesNotExist:
            return HttpResponse(status=404)

        # getting settings
        client_backend = ClientBackend.objects.get(client=p.client, backend=p.backend)
        cp = client_backend.get_config_parser()

        mrh_pass2 = cp.get('auth', 'pass1')

        summ = form.cleaned_data['OutSum']
        outer_checksum = form.cleaned_data['SignatureValue'].upper()
        my_checksum = sign(summ, payment_id, mrh_pass2).upper()

        if outer_checksum == my_checksum:
            raise FormOkException(payment=p)

    return HttpResponse('invalid form', status=400)

def success(request):
    try:
        return _success_fail_request_helper(request)
    except FormOkException as ex:
        payment = ex.payment
        payment.status = Payment.STATUS_SUCCESS
        payment.save()
        url = payment.success_url
        if url:
            return HttpResponseRedirect(url)
        else:
            return HttpResponse('payment successful', status=200)

def fail(request):
    try:
        return _success_fail_request_helper(request)
    except FormOkException as ex:
        payment = ex.payment
        payment.status = Payment.STATUS_FAILED
        payment.save()
        url = payment.fail_url
        if url:
            return HttpResponseRedirect(url)
        else:
            return HttpResponse('payment failed', status=200) # TODO: status?
