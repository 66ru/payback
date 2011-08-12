#-*- coding: UTF-8 -*-
from decimal import Decimal
import json
from django.core.urlresolvers import reverse

from django.test import TestCase
from django.test.client import Client as InternetClient
from cashflow.models import *

class SimpleTest(TestCase):
    def setUp(self):
        user = User.objects.create_user('test', 'test', password='test')
        self.user = user

        client_user = Client(user=user)
        client_user.save()
        self.client_user = client_user

        self.payment_backend = PaymentBackend()
        self.payment_backend.save()
        self.cur = Currency(title='Ya money', code='YANDEX', payment_backend=self.payment_backend)
        self.cur.save()

    def tearDown(self):
        self.client_user.delete()
        self.user.delete()
        self.payment_backend.delete()
        self.cur.delete()

    def test_listing(self):
        listing = Currency.get_listing()
        self.assertTrue(self.cur.code in listing)

    def test_list_rest(self):
        c = InternetClient()
        url = reverse('currs_list')
        annon_resp = c.post(url, {})
        self.assertEqual(annon_resp.status_code, 403)

        c.login(username='test', password='test')
        logged_in_resp = c.post(url, {})
        o = json.loads(logged_in_resp.content)
        self.assertTrue(self.cur.code in o['currs_list'])

    def test_create_payment_rest(self):
        c = InternetClient()
        url = reverse('create_payment')

        annon_resp = c.post(url, {})
        self.assertEqual(annon_resp.status_code, 403)

        c.login(username='test', password='test')
        # все четко
        params = {
            'amount': 42.50,
            'currency_code': self.cur.code,
            'comment': 'za gaz',
            'success_url': 'http://66.ru/success/',
            'fail_url': 'http://66.ru/fail/',
        }
        req = c.post(url, params)
        result = json.loads(req.content)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['payment_id'], 1)
        p = Payment.objects.get(pk=1)
        self.assertEqual(p.amount, Decimal('42.5'))
        self.assertEqual(p.currency, self.cur)
        self.assertEqual(p.backend, self.payment_backend)
        self.assertEqual(p.client, self.client_user)


        # все по минимуму
        params = {
            'amount': 42.50,
            'currency_code': self.cur.code,
        }
        req1 = c.post(url, params)
        result = json.loads(req1.content)
        self.assertEqual(result['status'], 'ok')
        p = Payment.objects.get(pk=2)
        self.assertEqual(p.amount, Decimal('42.5'))
        self.assertEqual(p.currency, self.cur)

        self.assertEqual(p.backend, self.payment_backend)
        self.assertEqual(p.client, self.client_user)
        self.assertEqual(p.comment, '')
        self.assertEqual(p.success_url, '')
        self.assertEqual(p.fail_url, '')

        # просто плохая форма
        params = {}
        req2 = c.post(url, params)
        result = json.loads(req2.content)
        self.assertEqual(result['status'], 'invalid form')

        # вариант со странной валютой
        params = {
            'amount': 42.50,
            'currency_code': 'PAPER',
        }
        req3 = c.post(url, params)
        result = json.loads(req3.content)
        self.assertEqual(result['status'], 'invalid form')

        # вариант с отрицательным числом
        params = {
            'amount': -200,
            'currency_code': self.cur.code,
        }
        req4 = c.post(url, params)
        result = json.loads(req4.content)
        self.assertEqual(result['status'], 'invalid form')

        # вариант со строкой вместо числа
        params = {
            'amount': 'yahrr!',
            'currency_code': self.cur.code,
        }
        req5 = c.post(url, params)
        result = json.loads(req5.content)
        self.assertEqual(result['status'], 'invalid form')
