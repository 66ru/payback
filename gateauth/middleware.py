# -*- coding: UTF-8 -*-
from models import User

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
            user = User.objects.get(signature=sign)
        except User.DoesNotExist:
            return

        try:
            tokens = User.tokens_range(-1, 1, params, unicode(sign))
        except TypeError:
            return

        if token in tokens:
            request.user = user.name

        return