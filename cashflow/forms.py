from django import forms
from models import Currency

class PaymentForm(forms.Form):
    amount = forms.DecimalField()
    currency_code = forms.ChoiceField(choices=[(c, c) for c in Currency.get_listing()])
    comment = forms.CharField(required=False)
    success_url = forms.URLField(required=False)
    fail_url = forms.URLField(required=False)