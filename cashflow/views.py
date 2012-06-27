#-*- coding: UTF-8 -*-
from functools import wraps
import json
from django.http import HttpResponse
from django.utils.decorators import available_attrs
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from cashflow.backends.common import SendPaymentFailureException, RedirectNeededException
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
@csrf_exempt
@require_http_methods(["POST"])
def currs_list(request):
    currs = [[c.code, c.title] for c in Currency.objects.filter(backend__isnull=False)]
    return response_json({'currs_list': currs})


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

        ret = {'payment_id': p.id}
        module = p.get_module(fromlist=['send_payment'])
        try:
            module.send_payment(p) # для систем без редиректов нужен будет рефакторинг (например, новый Exception)
        except RedirectNeededException as ex:
            ret['status'] = 'ok'
            ret['redirect_url'] = ex.get_url()
        except SendPaymentFailureException as ex:
            p.status = Payment.STATUS_FAILED
            p.status_message = ex.get_message()
            ret['status'] = 'failed'
            ret['status_message'] = p.status_message
        finally:
            p.save()

        return response_json(ret)

    return response_json({
        'status': 'invalid form',
        'form_errors': form.errors,
        'data': form.data,
    })


@login_required_403
@csrf_exempt
def status(request, id):
    try:
        p = Payment.objects.get(pk=id)
        if p.client.user != request.user:
            return HttpResponse(status=403)
    except Payment.DoesNotExist:
        return HttpResponse(status=404)

    return response_json({
        'status': p.get_status(),
        'status_message': p.status_message,
    })


def _create_success_or_fail(str_type):
    def _helper(request, backend_slug):
        try:
            b = Backend.objects.get(slug=backend_slug)
        except Backend.DoesNotExist:
            return HttpResponse(status=404)

        module = b.get_module(fromlist=[str_type])
        f = getattr(module, str_type)
        return f(request)

    return _helper

success = csrf_exempt(_create_success_or_fail('success'))
fail = csrf_exempt(_create_success_or_fail('fail'))
