from django.contrib import admin
from .models import *


admin.site.register(Backend)
admin.site.register(Client)
admin.site.register(ClientBackend)
admin.site.register(Currency)
admin.site.register(Payment)
