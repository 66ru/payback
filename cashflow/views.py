#-*- coding: UTF-8 -*-
from functools import wraps
import json
from django.http import HttpResponse
from django.utils.decorators import available_attrs
from django.utils.http import urlquote
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from cashflow.forms import PaymentForm
from models import *

def response_json(some_obj):
    return HttpResponse(json.dumps(some_obj), mimetype='application/javascript')

def user_passes_test_403(test_func):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """

    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            path = urlquote(request.get_full_path())
            return HttpResponse(status=403)
        return wraps(view_func, assigned=available_attrs(view_func))(_wrapped_view)
    return decorator


def login_required_403(function=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test_403(lambda u: u.is_authenticated())
    if function:
        return actual_decorator(function)
    return actual_decorator

@login_required_403
def currs_list(request):
    return response_json({
        'currs_list': Currency.get_listing()
    })


@login_required_403
@csrf_exempt
@require_http_methods(["POST"])
def create_payment(request):
    form = PaymentForm(request.POST)
    if form.is_valid():
        user = request.user
        amount = form.cleaned_data['amount']
        comment = form.cleaned_data['comment']
        currency_code = form.cleaned_data['currency_code']
        fail_url = form.cleaned_data['fail_url']
        success_url = form.cleaned_data['success_url']

        p = Payment.create(user, amount, currency_code, comment, success_url, fail_url)
        return response_json({
            'status': 'ok',
            'payment_id': p.id
        })
    return response_json({'status': 'invalid form', 'data': form.data})


def success(request):
    pass


def fail(request):
    pass