#-*- coding: UTF-8 -*-
from decimal import Decimal
import json
from django.core.urlresolvers import reverse

from django.test import TestCase
from django.test.client import Client as InternetClient
from cashflow.models import *

class BaseRESTTest(TestCase):
    def setUp(self):
        user = User.objects.create_user('test', 'test', password='test')
        self.user = user

        client_user = Client(user=user)
        client_user.save()
        self.client_user = client_user

        self.payment_backend = PaymentBackend(module='cashflow.backends.test_backend', slug='test')
        self.payment_backend.save()
        self.cur = Currency(title='Ya money', code='YANDEX', payment_backend=self.payment_backend)
        self.cur.save()

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
        PaymentBackend.objects.all().delete()
        Currency.objects.all().delete()


class ListingTest(BaseRESTTest):
    def setUp(self):
        super(ListingTest, self).setUp()
        self.url = reverse('currs_list')

    def test_listing_in_model(self):
        listing = Currency.get_listing()
        self.assertTrue(self.cur.code in listing)

    def test_list_rest(self):
        annon_resp = self.post({})
        self.assertEqual(annon_resp.status_code, 403)

        self.c.login(username='test', password='test')
        logged_in_resp = self.c.post(self.url, {})
        o = json.loads(logged_in_resp.content)
        self.assertTrue(self.cur.code in o['currs_list'])


class CreatePaymentTest(BaseRESTTest):
    def setUp(self):
        super(CreatePaymentTest, self).setUp()
        self.url = reverse('create_payment')

    def test_backend_changed(self):
        p = Payment.create(self.user, 23, self.cur.code)
        self.assertEqual(p.backend, self.payment_backend)

        new_backend = PaymentBackend(slug='test2')
        new_backend.save()
        self.cur.payment_backend = new_backend
        self.cur.save()

        self.assertEqual(p.backend, self.payment_backend)

        p2 = Payment.create(self.user, 24, self.cur.code)
        self.assertEqual(p2.backend, new_backend)


    def test_create_payment_rest_annon403(self):
        annon_resp = self.c.post(self.url, {})
        self.assertEqual(annon_resp.status_code, 403)

    def test_create_payment_rest_ok(self):
        self.login()
        # все четко
        params = {
            'amount': 42.50,
            'currency_code': self.cur.code,
            'comment': 'za gaz',
            'success_url': 'http://66.ru/success/',
            'fail_url': 'http://66.ru/fail/',
        }
        req = self.post(params)
        result = json.loads(req.content)
        self.assertEqual(result['status'], 'ok')
        p = Payment.objects.get()
        self.assertEqual(p.amount, Decimal('42.5'))
        self.assertEqual(p.currency, self.cur)
        self.assertEqual(p.backend, self.payment_backend)
        self.assertEqual(p.client, self.client_user)
        self.assertEqual(p.status, Payment.STATUS_SUCCESS)


    def test_create_payment_rest_minimum(self):
        self.login()
        # все по минимуму
        params = {
            'amount': 42.50,
            'currency_code': self.cur.code,
        }
        req = self.post(params)
        result = json.loads(req.content)
        self.assertEqual(result['status'], 'ok')
        p = Payment.objects.get()
        self.assertEqual(p.amount, Decimal('42.5'))
        self.assertEqual(p.currency, self.cur)

        self.assertEqual(p.backend, self.payment_backend)
        self.assertEqual(p.client, self.client_user)
        self.assertEqual(p.comment, '')
        self.assertEqual(p.success_url, '')
        self.assertEqual(p.fail_url, '')

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
            'currency_code': self.cur.code,
        }
        req = self.post(params)
        result = json.loads(req.content)
        self.assertEqual(result['status'], 'invalid form')

    def test_create_payment_rest_str_price(self):
        self.login()
        # вариант со строкой вместо числа
        params = {
            'amount': 'yahrr!',
            'currency_code': self.cur.code,
        }
        req5 = self.post(params)
        result = json.loads(req5.content)
        self.assertEqual(result['status'], 'invalid form')

class StatusTest(BaseRESTTest):
    def setUp(self):
        super(StatusTest, self).setUp()
        self.p = Payment.objects.create(amount=4000, currency=self.cur, client=self.client_user, backend=self.payment_backend)
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
