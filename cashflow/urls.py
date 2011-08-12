# -*- coding: UTF-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'currs_list$', 'cashflow.views.currs_list', name='currs_list'),
    url(r'create_payment', 'cashflow.views.create_payment', name='create_payment'),
)