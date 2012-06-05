# -*- coding: UTF-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('cashflow.views',
    url(r'currencies/$', 'currs_list', name='currs_list'),
    url(r'payments/add/', 'create_payment', name='create_payment'),
    url(r'payments/(?P<id>\d+)/$', 'status', name='payment_status'),
    url(r'payments/(?P<backend_slug>\w+)/success/$', 'success', name='payment_success'),
    url(r'payments/(?P<backend_slug>\w+)/fail/$', 'fail', name='payment_fail'),
)

#ya_money auth
urlpatterns += patterns('cashflow.backends.yandex_money_backend',
    url(r'payments/ya_auth/(?P<id>\d+)/$', 'ya_money_auth_payment', name='ya_money_auth_payment'),
)