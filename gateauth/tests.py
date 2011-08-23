# -*- coding: utf-8 -*-

from django.test.client import Client
from django.utils import unittest
from models import *
from datetime import datetime
import time

from django.http import HttpResponse

def test_view(request):
    return HttpResponse(str(request.user))

class AuthenticateTestCase(unittest.TestCase):
    def setUp(self):
        user = User.objects.create_user('test', 'test', password='test')
        self.user_hash = HashKey(user=user)
        self.user_hash.save()
        self.client = Client()

    def test_authenticate(self):

        params = {'a': 1, 'b': 2}

        resp = self.client.get('/gateauth/')
        self.assertEqual(resp.content, 'AnonymousUser')

        resp = self.client.get('/gateauth/', params)
        self.assertEqual(resp.content, 'AnonymousUser')

        resp = self.client.get('/gateauth/', {'sign': self.user_hash.signature})
        self.assertEqual(resp.content, 'AnonymousUser')

        resp = self.client.get('/gateauth/', {'sign': self.user_hash.signature, 'token': 'ololo'})
        self.assertEqual(resp.content, 'AnonymousUser')

        fromtimestamp = datetime.fromtimestamp
        timestamp = time.time()
        date = HashKey.date2utc2str(fromtimestamp(timestamp))

        data = {'sign': self.user_hash.signature}
        data['token'] = HashKey.get_token({}, self.user_hash.signature, date)
        resp = self.client.get('/gateauth/', data)
        self.assertEqual(resp.content, self.user_hash.user.username)

        data['token'] = HashKey.get_token(params, self.user_hash.signature, date)
        data.update(params)
        resp = self.client.get('/gateauth/', data)
        self.assertEqual(resp.content, self.user_hash.user.username)

        data['signature'] = 'ololo'
        resp = self.client.get('/gateauth/', data)
        self.assertEqual(resp.content, 'AnonymousUser')