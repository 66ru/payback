from django.contrib import admin
from .models import *


admin.site.register(PaymentBackend)
admin.site.register(Client)
admin.site.register(Currency)
admin.site.register(Payment)
