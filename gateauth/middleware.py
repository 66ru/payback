# -*- coding: UTF-8 -*-
from models import HashKey

class PartnerPostTokenMiddleware(object):
    def process_request(self, request):
        if 'token' not in request.REQUEST or 'sign' not in request.REQUEST:
            return

        token = request.REQUEST['token']
        sign = request.REQUEST['sign']
        params = dict(request.REQUEST)

        del params['token']
        del params['sign']

        try:
            user_hashkey = HashKey.objects.get(signature=sign)
        except HashKey.DoesNotExist:
            return

        try:
            tokens = HashKey.tokens_range(-1, 1, params, unicode(sign))
        except TypeError:
            return

        if token in tokens:
            request.user = user_hashkey.user

        return