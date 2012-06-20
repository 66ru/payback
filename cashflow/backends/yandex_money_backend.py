#-*- coding: utf-8 -*-
import urllib, urllib2
import json
import time
from django.http import HttpResponse, HttpResponseRedirect
from common import CashflowBaseException
from cashflow.backends.common import RedirectNeededException
from cashflow.models import Payment, ClientBackend
from cashflow.views import login_required_403

###
# config:
#
# ...
# [yandex_money]
# account = yandex_account_number
# key = client_id
# redirect_uri = redirect_uri
# 41001461963445 my account number
# 31B48E2D251B3DD402339B95EEB5D0DA8C4B566BB271DD9641060900E48ED415 my code
# http://payback.gpor.ru/ my redirect uri

class ChangeToPermanentTokenException(CashflowBaseException):
    pass

def _get_url_yandex_money_auth(ya_account, api_key, redirect_uri, payment):
    url = 'https://sp-money.yandex.ru/oauth/authorize'

    data = {
        'client_id': api_key,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope': 'payment.to-account("%s").limit(,%s)' % (ya_account, payment.amount)
        }

    url += '?' + urllib.urlencode(data)
    return url

def _get_permanent_token_auth(request, code, api_key, redirect_uri):
    url = 'https://sp-money.yandex.ru/oauth/token'
    data = {
        'code': code,
        'client_id': api_key,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
    }

    fs = urllib2.urlopen(url, urllib.urlencode(data))
    resp = json.load(fs)

    if resp.get('access_token') is None:
        raise ChangeToPermanentTokenException(message=resp.get('error'))

    return resp.get('access_token')

def _payment_proceed(payment, access_token):
    while payment.status == Payment.STATUS_IN_PROGRESS:
        url = 'https://money.yandex.ru/api/process-payment'
        data = {'request_id': payment.status_message}
        rq = urllib2.Request(url)
        rq.add_header('Authorization', 'Bearer ' + access_token)

        fs = urllib2.urlopen(rq, urllib.urlencode(data))
        resp = json.load(fs)

        status = resp.get('status')
        if status == 'success':
            payment.status = Payment.STATUS_SUCCESS
            payment.status_message = 'payment_id: %s' % resp.get('payment_id')
        elif status == 'refused':
            payment.status = Payment.STATUS_FAILED
            payment.status_message = resp.get('error')
        else:
            time.sleep(1)

    return payment

@login_required_403
def ya_money_auth_payment(request):
    id = request.GET.get('p')
    code = request.GET.get('code')
    error = request.GET.get('error')

    payment = Payment.objects.get(pk=id)
    client_backend = ClientBackend.objects.get(client=payment.client, backend=payment.backend)
    cp = client_backend.get_config_parser()

    ya_account = cp.get('yandex_money', 'account')
    api_key = cp.get('yandex_money', 'key')
    redirect_uri = cp.get('yandex_money', 'redirect_uri')

    comment = payment.comment
    if isinstance(comment, unicode):
        payment_comment = comment.encode('utf8')

    if not code:
        payment.status = Payment.STATUS_FAILED
        payment.status_message = error
    else:
        try:
            access_token = _get_permanent_token_auth(request, code, api_key, redirect_uri)
        except ChangeToPermanentTokenException, ex:
            payment.status = Payment.STATUS_FAILED
            payment.status_message = ex.get_message()
        #requesting payment
        else:
            rq = urllib2.Request('https://money.yandex.ru/api/request-payment')
            rq.add_header('Authorization', 'Bearer ' + access_token)
            data = {
                'pattern_id': 'p2p',
                'to': ya_account,
                'amount': payment.amount,
                'comment': payment_comment,
                'message': payment_comment,
            }
            fs = urllib2.urlopen(rq, urllib.urlencode(data))
            resp = json.load(fs)

            req_payment_status = resp.get('status')

            if req_payment_status == 'success':
                payment.status = Payment.STATUS_IN_PROGRESS
                payment.status_message = resp.get('request_id')
#                payment = _payment_proceed(payment, access_token)
            else:
                payment.status = Payment.STATUS_FAILED
                payment.status_message = resp.get('error_description')

    payment.save()

    if payment.status == Payment.STATUS_SUCCESS:
        redirect_url = payment.success_url
        subj = 'payment successful'
    else:
        redirect_url = payment.fail_url
        subj = 'payment failed'

    if redirect_url:
        return HttpResponseRedirect(redirect_url)
    else:
        return HttpResponse(subj, 200)


def send_payment(payment):
    client_backend = ClientBackend.objects.get(client=payment.client, backend=payment.backend)
    cp = client_backend.get_config_parser()

    ya_account = cp.get('yandex_money', 'account')
    api_key = cp.get('yandex_money', 'key')
    redirect_uri = cp.get('yandex_money', 'redirect_uri')
    if redirect_uri:
        if not redirect_uri.endswith('/'):
            redirect_uri += '/'
        redirect_uri += '?p=%s' % payment.id
    url = _get_url_yandex_money_auth(ya_account, api_key, redirect_uri, payment)

    raise RedirectNeededException(url, '(yandex money auth): %s' % url)


def success(request):
    return HttpResponse('payment successful', status=200)

def fail(request):
    return HttpResponse('payment failed', status=200)