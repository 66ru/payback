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
        self.user = User(name='vasya', signature='pupkin')
        self.user.save()
        self.client = Client()

    def test_authenticate(self):

        params = {'a': 1, 'b': 2}

        resp = self.client.get('/gateauth/')
        self.assertEqual(resp.content, 'AnonymousUser')

        resp = self.client.get('/gateauth/', params)
        self.assertEqual(resp.content, 'AnonymousUser')

        resp = self.client.get('/gateauth/', {'sign': self.user.signature})
        self.assertEqual(resp.content, 'AnonymousUser')

        resp = self.client.get('/gateauth/', {'sign': self.user.signature, 'token': 'ololo'})
        self.assertEqual(resp.content, 'AnonymousUser')

        fromtimestamp = datetime.fromtimestamp
        timestamp = time.time()
        date = User.date2utc2str(fromtimestamp(timestamp))

        data = {'sign': self.user.signature}
        data['token'] = User.get_token({}, self.user.signature, date)
        resp = self.client.get('/gateauth/', data)
        self.assertEqual(resp.content, self.user.name)

        data['token'] = User.get_token(params, self.user.signature, date)
        data.update(params)
        resp = self.client.get('/gateauth/', data)
        self.assertEqual(resp.content, self.user.name)

        data['signature'] = 'ololo'
        resp = self.client.get('/gateauth/', data)
        self.assertEqual(resp.content, 'AnonymousUser')