#-*- coding: UTF-8 -*-
from django.db import models


class Currency(models.Model):
    # TODO: надо ссылку на конкретную кассу, которой будем слать...
    code = models.CharField(max_length=15) # для распознавания в запросах пользователей


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

    # TODO: client id
    amount = models.DecimalField()
    currency = models.ForeignKey(Currency)
    created = models.DateTimeField(auto_now_add=True)
    comment = models.TextField()
    success_url = models.URLField()
    fail_url = models.URLField()
    status = models.CharField(max_length=1)
    status_message = models.TextField()


    class Meta:
        permissions = (('view_payment', 'Can view payments'),)


    def __unicode__(self):
        return '%s %s' % (self.amount, self.currency,)