from django.conf.urls.defaults import *

import cashflow.urls
import gateauth.urls

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^payback/', include('payback.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^c/', include(cashflow.urls)),
    (r'^gateauth/', include(gateauth.urls)),
    (r'^mobi_money_service/', 'cashflow.backends.mobi_money_backend.mobi_money_service'),
)
