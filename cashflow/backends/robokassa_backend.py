#-*- coding: UTF-8 -*-
from hashlib import md5
from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from cashflow.models import Payment, ClientBackend

###
# config:
#
# [auth]
# pass1 = someting1
# pass2 = someting2
#


def sign(summ, inv_id, pwd):
    return md5(':'.join((str(summ), str(inv_id), pwd,))).hexdigest().upper()

def send_payment(payment):
    return True

class SuccessForm(forms.Form):
    OutSum = forms.DecimalField(min_value=0)
    InvId = forms.IntegerField(min_value=1)
    SignatureValue = forms.CharField(max_length=32)

def success(request):
    form = SuccessForm(request.POST)
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
            p.status = Payment.STATUS_SUCCESS
            p.save()

            url = p.success_url
            if url:
                return HttpResponseRedirect(url)
            else:
                return HttpResponse('payment successful', status=200)

    return HttpResponse('invalid form', status=400)


def fail(_):
    return HttpResponse('so?', status=200)