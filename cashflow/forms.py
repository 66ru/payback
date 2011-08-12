from django import forms

class PaymentForm(forms.Form):
    amount = forms.DecimalField()
    currency_code = forms.SlugField()
    comment = forms.CharField(required=False)
    success_url = forms.URLField(required=False)
    fail_url = forms.URLField(required=False)