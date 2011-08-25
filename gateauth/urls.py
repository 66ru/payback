# -*- coding: UTF-8 -*-

from django.conf.urls.defaults import *

urlpatterns = patterns('gateauth.tests',
    url(r'^$', 'test_view', name='test_view'),
)