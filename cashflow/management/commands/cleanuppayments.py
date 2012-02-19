from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db.models import Q
from cashflow.models import Payment

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        now = datetime.now()
        valid_datetime = now - timedelta(hours=2)
        non_valid_payments = Payment.objects.filter(
            Q(created__lt=valid_datetime),
            Q(status=Payment.STATUS_IN_PROGRESS) | Q(status=Payment.STATUS_FAILED)
        )
        non_valid_payments.delete()
