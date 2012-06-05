#-*- coding: utf-8 -*-
import urllib
import json
from cashflow.backends.common import RedirectNeededException
from cashflow.models import Payment, ClientBackend
from cashflow.views import login_required_403, response_json

###
# config:
#
# ...
# [yandex_money]
# key = key
# redirect_uri = redirect_uri
# 31B48E2D251B3DD402339B95EEB5D0DA8C4B566BB271DD9641060900E48ED415 my code
# http://payback.gpor.ru/ my redirect uri

class RedirectAuthException(Exception):
    def __init__(self, url, message, *args, **kwargs):
        super(RedirectAuthException, self).__init__(message, *args, **kwargs)
        self.url = url

    def get_url(self):
        return self.url

def _get_url_yandex_money_auth(api_key, redirect_uri, payment):
    url = 'https://sp-money.yandex.ru/oauth/authorize'
    data = {
        'client_id': api_key,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope': 'payment.to-pattern("%s").limit(, %s)' % (payment.comment, payment.amount), #authorize request to payment
        }

    if not url.endswith('/'):
        url += '/'
    url += '%s/' % payment.id + '?' + urllib.urlencode(data)
    return url


@login_required_403
def ya_money_auth_payment(request, id):
    payment = Payment.objects.get(pk=id)
    client_backend = ClientBackend.objects.get(client=payment.client, backend=payment.backend)
    cp = client_backend.get_config_parser()

    code = request.GET.get('code')
    error = request.GET.get('error')

    api_key = cp.get('yandex_money', 'key')

    if code:
        url = 'https://sp-money.yandex.ru/oauth/token'
        data = {
            'code': code,
            'client_id': api_key,
            'grant_type': 'authorization_code',
            'redirect_uri': request.META['REQUEST_URI']
        }

        fs = urllib.urlopen(url, urllib.urlencode(data))
        resp = json.load(fs)
        access_token = resp.get('access_token')
        access_error = resp.get('error')

        if access_token:
            response_json({'access_token': access_token})

        response_json({'error': access_error})

    response_json({'error': error})


def send_payment(payment):
    client_backend = ClientBackend.objects.get(client=payment.client, backend=payment.backend)
    cp = client_backend.get_config_parser()

    api_key = cp.get('yandex_money', 'key')
    redirect_uri = cp.get('yandex_money', 'redirect_uri')
    url = _get_url_yandex_money_auth(api_key, redirect_uri, payment)

    raise RedirectNeededException(url, '(yandex money auth): %s' % url)


def success(request):
    return True

def fail(request):
    return True