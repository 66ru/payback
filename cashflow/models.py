#-*- coding: UTF-8 -*-
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models


class PaymentBackend(models.Model):
    module = models.CharField(max_length=100,
                              choices=[(g, g)
                                        for g in settings.PAYMENT_BACKENDS_ENABLED])

    def __unicode__(self):
        return self.module


class Client(models.Model):
    user = models.OneToOneField(User)
    backend_settings = models.ManyToManyField(PaymentBackend, through='PaymentBackend_Client')


class PaymentBackend_Client(models.Model):
    client = models.ForeignKey(Client)
    payment_backend = models.ForeignKey(PaymentBackend)

    settings = models.TextField()

    class Meta:
        unique_together = ('client', 'payment_backend',)
    

class Currency(models.Model):
    title = models.CharField(max_length=50)
    code = models.CharField(max_length=15) # для распознавания в запросах пользователей
    payment_backend = models.ForeignKey(PaymentBackend)

    def __unicode__(self):
        return '%s: %s' % (self.code, self.title,)


# Create your models here.
class Payment(models.Model):
    STATUS_IN_PROGRESS = '0'
    STATUS_SUCCESS = '1'
    STATUS_FAILED_INNER = '2'
    STATUS_FAILED_PROVIDER = '3'

    STATUS_CHOICES = (
            (STATUS_IN_PROGRESS, 'IN PROGRESS'),
            (STATUS_SUCCESS, 'OK'),
            (STATUS_FAILED_INNER, 'INNER FAILURE'),
            (STATUS_FAILED_PROVIDER, 'PROVIDER FAILURE'),
        )

    # TODO: client
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey(Currency)
    # TODO: backend (не должен меняться, если что-то поменяется в валюте)
    created = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True)
    success_url = models.URLField(blank=True)
    fail_url = models.URLField(blank=True)
    status = models.CharField(max_length=1, default=STATUS_IN_PROGRESS)
    status_message = models.TextField(blank=True)


    class Meta:
        permissions = (('view_payment', 'Can view payments'),)


    def __unicode__(self):
        return '%s %s' % (self.amount, self.currency,)