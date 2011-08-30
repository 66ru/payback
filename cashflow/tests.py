#-*- coding: UTF-8 -*-
from decimal import Decimal
import json
from django.core.urlresolvers import reverse

from django.test import TestCase
from django.test.client import Client as InternetClient
from cashflow.backends.common import RedirectNeededException
from cashflow.backends.robokassa_backend import sign as robo_sign, send_payment as robo_send_payment
from cashflow.models import *

class BaseRESTTest(TestCase):
    def setUp(self):
        user = User.objects.create_user('test', 'test', password='test')
        self.user = user

        client_user = Client(user=user)
        client_user.save()
        self.client_user = client_user

        self.test_backend = Backend(module='cashflow.backends.test_backend', slug='test')
        self.test_backend.save()
        self.yamoney = Currency(title='Ya money', code='YANDEX', backend=self.test_backend)
        self.yamoney.save()

        self.c = InternetClient()

        self.url = None

    def post(self, params):
        return self.c.post(self.url, params)

    def login(self):
        self.c.login(username='test', password='test')

    def tearDown(self):
        self.c.logout()
        Client.objects.all().delete()
        User.objects.all().delete()
        Backend.objects.all().delete()
        Currency.objects.all().delete()


class RoboTest(BaseRESTTest):
    def setUp(self):
        super(RoboTest, self).setUp()

        self.robo_backend = Backend(module='cashflow.backends.robokassa_backend', slug='robo')
        self.robo_backend.save()

        # доселе неизвестная валюта...
        self.robomoney = Currency(title='Robo money yall!', code='ROBO', backend=self.robo_backend)
        self.robomoney.save()

        self.client_login = 'some_login'
        self.pass1 = 'something1'
        self.pass2 = 'something2'

        client_settings = ClientBackend(client=self.client_user, backend=self.robo_backend)
        client_settings.settings = \
        ("[auth]\n" +
         "login = %s\n" +
         "pass1 = %s\n" +
         "pass2 = %s\n") % (self.client_login, self.pass1, self.pass2,)
        client_settings.save()
        self.client_settings = client_settings

        p = Payment()
        p.client = self.client_user
        p.amount = Decimal('300')
        p.currency = self.robomoney
        p.backend = self.robo_backend
        p.success_url = 'http://example.com/'
        p.save()
        self.payment = p

        self.success_url_to_trigger = reverse('payment_success', args=[self.robo_backend.slug])

    @staticmethod
    def _create_robo_request_params(payment_id, summ, signature):
        return {
            'InvId': payment_id,
            'OutSum': summ,
            'SignatureValue': signature,
        }

    def test_client_settings(self):
        cp = self.client_settings.get_config_parser()
        self.assertEquals(cp.get('auth', 'pass1'), self.pass1)
        self.assertEquals(cp.get('auth', 'pass2'), self.pass2)

    def test_trigger_success_ok(self): # робокасса дергает урл success'а
        self.assertEqual(self.payment.status, Payment.STATUS_IN_PROGRESS)

        payment_id = self.payment.id
        amount = self.payment.amount
        signature = robo_sign(amount, payment_id, self.pass1)

        params = self._create_robo_request_params(payment_id,
                                                  amount,
                                                  signature)

        req = self.c.post(self.success_url_to_trigger, data=params)
        self.assertEqual(req.status_code, 302)

    def test_trigger_success_ok_no_url(self): # робокасса дергает урл success'а (в пэементе нет ссылки на успешный урл)
        self.assertEqual(self.payment.status, Payment.STATUS_IN_PROGRESS)

        payment_id = self.payment.id
        amount = self.payment.amount
        signature = robo_sign(amount, payment_id, self.pass1)

        params = self._create_robo_request_params(payment_id,
                                                  amount,
                                                  signature)
        self.payment.success_url = ''
        self.payment.save()

        req = self.c.post(self.success_url_to_trigger, data=params)
        self.assertEqual(req.status_code, 200)

    def test_trigger_success_no_signature_400(self):
        payment_id = self.payment.id
        amount = self.payment.amount

        params = self._create_robo_request_params(payment_id,
                                                  amount,
                                                  '')
        del params['SignatureValue']

        req = self.c.post(self.success_url_to_trigger, data=params)
        self.assertEqual(req.status_code, 400)

    def test_trigger_success_bad_signature(self):
        payment_id = self.payment.id
        amount = self.payment.amount

        params = self._create_robo_request_params(payment_id,
                                                  amount,
                                                  'badasssignature')
        req = self.c.post(self.success_url_to_trigger, data=params)
        self.assertEqual(req.status_code, 400)

    def test_send_payment(self):
        payment_sender = lambda: robo_send_payment(self.payment)
        self.assertRaises(RedirectNeededException, payment_sender)


class ListingTest(BaseRESTTest):
    def setUp(self):
        super(ListingTest, self).setUp()
        self.url = reverse('currs_list')

    def test_listing_in_model(self):
        listing = Currency.get_listing()
        self.assertTrue(self.yamoney.code in listing)

    def test_list_rest(self):
        annon_resp = self.post({})
        self.assertEqual(annon_resp.status_code, 403)

        self.c.login(username='test', password='test')
        logged_in_resp = self.c.post(self.url, {})
        o = json.loads(logged_in_resp.content)
        self.assertTrue(self.yamoney.code in o['currs_list'])


class CreatePaymentTest(BaseRESTTest):
    def setUp(self):
        super(CreatePaymentTest, self).setUp()
        self.url = reverse('create_payment')

    def test_backend_changed(self):
        p = Payment.create(self.user, 23, self.yamoney.code)
        self.assertEqual(p.backend, self.test_backend)

        new_backend = Backend(slug='test2')
        new_backend.save()
        self.yamoney.backend = new_backend
        self.yamoney.save()

        self.assertEqual(p.backend, self.test_backend)

        p2 = Payment.create(self.user, 24, self.yamoney.code)
        self.assertEqual(p2.backend, new_backend)

    def test_create_payment_rest_annon403(self):
        annon_resp = self.c.post(self.url, {})
        self.assertEqual(annon_resp.status_code, 403)

    def test_create_payment_rest_ok(self):
        self.login()
        # все четко
        params = {
            'amount': 42.50,
            'currency_code': self.yamoney.code,
            'comment': 'za gaz',
            'success_url': 'http://66.ru/success/',
            'fail_url': 'http://66.ru/fail/',
        }
        req = self.post(params)
        result = json.loads(req.content)
        self.assertEqual(result['status'], 'ok')
        p = Payment.objects.get()
        self.assertEqual(p.amount, Decimal('42.5'))
        self.assertEqual(p.currency, self.yamoney)
        self.assertEqual(p.backend, self.test_backend)
        self.assertEqual(p.client, self.client_user)
        self.assertEqual(p.status, Payment.STATUS_IN_PROGRESS)
        self.assertEqual(p.id, result['payment_id'])

    def test_create_payment_rest_minimum(self):
        self.login()
        # все по минимуму
        params = {
            'amount': 42.50,
            'currency_code': self.yamoney.code,
        }
        req = self.post(params)
        result = json.loads(req.content)
        self.assertEqual(result['status'], 'ok')
        p = Payment.objects.get()
        self.assertEqual(p.amount, Decimal('42.5'))
        self.assertEqual(p.currency, self.yamoney)

        self.assertEqual(p.backend, self.test_backend)
        self.assertEqual(p.client, self.client_user)
        self.assertEqual(p.comment, '')
        self.assertEqual(p.success_url, '')
        self.assertEqual(p.fail_url, '')
        self.assertEqual(p.id, result['payment_id'])

    def test_create_payment_rest_empty_form(self):
        self.login()
        # просто плохая форма
        params = {}
        req = self.post(params)
        result = json.loads(req.content)
        self.assertEqual(result['status'], 'invalid form')

    def test_create_payment_rest_silly_cur(self):
        self.login()
        # вариант со странной валютой
        params = {
            'amount': 42.50,
            'currency_code': 'PAPER',
        }
        req3 = self.post(params)
        result = json.loads(req3.content)
        self.assertEqual(result['status'], 'invalid form')

    def test_create_payment_negative_amount(self):
        self.login()
        # вариант с отрицательным числом
        params = {
            'amount': -200,
            'currency_code': self.yamoney.code,
        }
        req = self.post(params)
        result = json.loads(req.content)
        self.assertEqual(result['status'], 'invalid form')

    def test_create_payment_rest_str_price(self):
        self.login()
        # вариант со строкой вместо числа
        params = {
            'amount': 'yahrr!',
            'currency_code': self.yamoney.code,
        }
        req5 = self.post(params)
        result = json.loads(req5.content)
        self.assertEqual(result['status'], 'invalid form')


class StatusTest(BaseRESTTest):
    def setUp(self):
        super(StatusTest, self).setUp()
        self.p = Payment.objects.create(amount=4000, currency=self.yamoney, client=self.client_user, backend=self.test_backend)
        self.url = reverse('payment_status', args=[self.p.id])

    def test_status_annon(self):
        result = self.c.get(self.url)
        self.assertEqual(result.status_code, 403)

    def test_status_404(self):
        self.login()
        result = self.c.get(reverse('payment_status', args=[10000]))
        self.assertEqual(result.status_code, 404)

    def test_status_ok(self):
        self.login()
        result = self.c.get(self.url)
        self.assertEqual(result.status_code, 200)
        result_o = json.loads(result.content)
        self.assertEqual(result_o['status'], 'IN PROGRESS')


class SuccessFailTest(BaseRESTTest):
    def test_unknown_backend_404(self):
        result = self.c.get(reverse('payment_success', args=['UNKNOWN_BACKEND_SLUG_YALL']))
        self.assertEqual(result.status_code, 404)

        result = self.c.get(reverse('payment_fail', args=['UNKNOWN_BACKEND_SLUG_YALL']))
        self.assertEqual(result.status_code, 404)
