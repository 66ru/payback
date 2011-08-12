# -*- coding: UTF-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'currs_list$', 'cashflow.views.currs_list'),
    (r'create_payment', 'cashflow.views.create_payment'),
)