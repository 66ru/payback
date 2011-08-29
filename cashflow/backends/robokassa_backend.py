#-*- coding: UTF-8 -*-
from hashlib import md5
from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from cashflow.backends.common import RedirectNeededException
from cashflow.models import Payment, ClientBackend

###
# config:
#
# [auth]
# login = login
# pass1 = someting1
# pass2 = someting2
#


def sign(summ, inv_id, pwd):
    return md5('%s:%s:%s' % (summ, inv_id, pwd,)).hexdigest().upper()

def send_payment(payment): # throws SendPaymentFailureException
    client_backend = ClientBackend.objects.get(client=payment.client, backend=payment.backend)
    cp = client_backend.get_config_parser()

    login = cp.get('auth', 'login')
    pwd = cp.get('auth', 'pass1')

    url = "https://merchant.roboxchange.com/Index.aspx" + \
          "?MrchLogin=%(login)s&OutSum=%(summ)s&" + \
          "InvId=%(inv_id)s&Desc=%(comment)s&" + \
          "SignatureValue=%(signature)s" % {
              'login': login,
              'summ' : payment.amount,
              'inv_id' : payment.id,
              'comment': payment.comment,
              'signature': sign(payment.amount, payment.id, pwd),
          }
    raise RedirectNeededException(url, '(send payment): %s' % url)


class ResultForm(forms.Form):
    OutSum = forms.DecimalField(min_value=0)
    InvId = forms.IntegerField(min_value=1)
    SignatureValue = forms.CharField(max_length=32)

class FormOkException(BaseException):
    def __init__(self, payment, *args, **kwargs):
        super(FormOkException, self).__init__(*args, **kwargs)
        self.payment = payment

def _success_fail_helper(request):
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

        mrh_pass2 = cp.get('auth', 'pass2')

        summ = form.cleaned_data['OutSum']
        outer_checksum = form.cleaned_data['SignatureValue'].upper()
        my_checksum = sign(summ, payment_id, mrh_pass2)

        if outer_checksum == my_checksum:
            raise FormOkException(payment=p)

    return HttpResponse('invalid form', status=400)

def success(request):
    try:
        return _success_fail_helper(request)
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
        return _success_fail_helper(request)
    except FormOkException as ex:
        payment = ex.payment
        payment.status = Payment.STATUS_FAILED
        payment.save()
        url = payment.fail_url
        if url:
            return HttpResponseRedirect(url)
        else:
            return HttpResponse('payment failed', status=200) # TODO: status?
