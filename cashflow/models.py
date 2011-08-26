#-*- coding: UTF-8 -*-
import ConfigParser
import io
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models


class Backend(models.Model):
    slug = models.SlugField(unique=True)
    module = models.CharField(max_length=100,
                              choices=[(g, g)
                                        for g in settings.PAYMENT_BACKENDS_ENABLED])

    def get_module(self, fromlist=['*']):
        return __import__(self.module, globals(), locals(), fromlist=fromlist, level=0)

    def __unicode__(self):
        return self.module


class Client(models.Model):
    user = models.OneToOneField(User)
    backend_settings = models.ManyToManyField(Backend, through='ClientBackend', related_name='bs')

    def __unicode__(self):
        return '%s client' % self.user


class ClientBackend(models.Model):
    client = models.ForeignKey(Client)
    backend = models.ForeignKey(Backend)

    settings = models.TextField()

    def get_config_parser(self):
        conf_parser = ConfigParser.RawConfigParser()
        conf_parser.readfp(io.BytesIO(str(self.settings)))
        return conf_parser

    def __unicode__(self):
        return '%s: %s' % (self.client, self.backend,)

    class Meta:
        unique_together = ('client', 'backend',)
    

class Currency(models.Model):
    title = models.CharField(max_length=50)
    code = models.SlugField(max_length=15, unique=True) # для распознавания в запросах пользователей
    backend = models.ForeignKey(Backend, blank=True, null=True)

    @classmethod
    def get_listing(cls):
        return [c.code for c in cls.objects.filter(backend__isnull=False)]

    def __unicode__(self):
        return '%s: %s' % (self.code, self.title,)


# Create your models here.
class Payment(models.Model):
    STATUS_IN_PROGRESS = '0'
    STATUS_SUCCESS = '1'
    STATUS_FAILED = '2'

    STATUS_CHOICES = (
            (STATUS_IN_PROGRESS, 'IN PROGRESS'),
            (STATUS_SUCCESS, 'OK'),
            (STATUS_FAILED, 'FAILED'),
        )

    client = models.ForeignKey(Client)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey(Currency)
    backend = models.ForeignKey(Backend)
    created = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True)
    success_url = models.URLField(blank=True)
    fail_url = models.URLField(blank=True)
    status = models.CharField(max_length=1, default=STATUS_IN_PROGRESS)
    status_message = models.TextField(blank=True)

    def get_module(self, fromlist=['*']):
        return self.backend.get_module(fromlist=fromlist)

    def get_status(self):
        status_dict = dict(self.STATUS_CHOICES)
        return status_dict[self.status]

    @classmethod
    def create(cls, user, amount, currency_code, comment='', success_url='', fail_url=''):
        client = Client.objects.get(user=user)
        currency = Currency.objects.get(code=currency_code)
        backend = currency.backend

        return Payment.objects.create(client=client,
                                      amount=amount,
                                      currency=currency,
                                      backend=backend,
                                      comment=comment,
                                      success_url=success_url,
                                      fail_url=fail_url)

    class Meta:
        permissions = (('view_payment', 'Can view payments'),)


    def __unicode__(self):
        return '%s %s' % (self.amount, self.currency,)