# -*- coding: UTF-8 -*-

from django.db import models
from django.contrib.auth.models import User
import string
import random
import hashlib
from datetime import datetime, timedelta
import time

def randstring_creator(count):
    def _randstring():
        a =  string.ascii_letters + string.digits
        return ''.join([random.choice(a) for _ in xrange(count)])

    return _randstring


class HashKey(models.Model):
    user = models.OneToOneField(User)
    code = models.SlugField(unique=True)
    key = models.CharField(max_length=20, unique=True, default=randstring_creator(20))

    @staticmethod
    def datetime2str(dt):
        return '%s%s%s%s' % (dt.year, dt.month, dt.day, dt.hour,)

    @staticmethod
    def sign(params, salt, date=None):
        items = sorted(params.iteritems())
        hash = u'&'.join([u'='.join((unicode(k), unicode(v))) for k, v in items])
        date = date or HashKey.datetime2str(datetime.utcnow())

        #прибаляем дату в формате UTC2 и применяем sha1
        s1 = u''.join((hash, date))
        hash = hashlib.sha1(s1).hexdigest()
        #добавляем ключ и применяем sha1
        hash = hashlib.sha1(u''.join((hash, salt))).hexdigest()

        return unicode(hash)

    @staticmethod
    def signs_range(params, salt):
        if not isinstance(params, dict) \
            or not isinstance(salt, basestring):
            raise TypeError

        utc_dates = [HashKey.datetime2str(datetime.utcnow() + timedelta(hours=a)) for a in xrange(-1, 2)]
        return [HashKey.sign(params, salt, dt) for dt in utc_dates]

    def __unicode__(self):
        return u'%s (partner)' % self.code
