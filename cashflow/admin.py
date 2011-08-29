from django.contrib import admin
from .models import *

class BackendsAdmin(admin.ModelAdmin):
    list_display = ('slug',)

admin.site.register(Backend, BackendsAdmin)
admin.site.register(Client)

class ClientBackendAdmin(admin.ModelAdmin):
    list_display = ('client', 'backend',)

admin.site.register(ClientBackend, ClientBackendAdmin)


class CurrencyBackend(admin.ModelAdmin):
    list_display = ('title', 'code', 'backend',)
admin.site.register(Currency, CurrencyBackend)

class PaymentsAdmin(admin.ModelAdmin):
    list_display = ('client', 'amount', 'currency', 'backend', 'comment', 'status',)

admin.site.register(Payment, PaymentsAdmin)
