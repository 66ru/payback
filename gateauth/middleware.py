# -*- coding: UTF-8 -*-
from models import HashKey

class PartnerPostTokenMiddleware(object):
    def process_request(self, request):
        if 'sign' not in request.REQUEST or 'code' not in request.REQUEST:
            return

        token = request.REQUEST['sign']
        code = request.REQUEST['code']
        params = dict(request.REQUEST)

        del params['sign']
        del params['code']

        try:
            user_hashkey = HashKey.objects.get(code=code)
        except HashKey.DoesNotExist:
            return

        try:
            tokens = HashKey.signs_range(-1, 1, params, user_hashkey.key)
        except TypeError:
            return

        if token in tokens:
            request.user = user_hashkey.user

        return