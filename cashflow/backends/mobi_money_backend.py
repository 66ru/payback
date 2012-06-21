# -*- coding: utf-8 -*-
from urlparse import parse_qs
from django.http import HttpResponse
from cashflow.models import Payment
from rpclib.server.django import DjangoApplication
from rpclib.model.primitive import String, Integer, DateTime, Float, Boolean
from rpclib.model.complex import  ComplexModel
from rpclib.service import ServiceBase
from rpclib.interface.wsdl import Wsdl11
from rpclib.protocol.soap import Soap11
from rpclib.application import Application
from rpclib.decorator import rpc
from django.views.decorators.csrf import csrf_exempt


class MobiMoneyService(ServiceBase):
    @rpc(String, DateTime,String, Boolean, _returns=(String, Float, String, Integer), _out_variable_names=('PayeeRegData', 'Sum', 'Contract', 'PaymentDelay'))
    def PaymentContract(ctx, PaymentID, PaymentTime, UserParams, Demo):
        user_params = parse_qs(UserParams)
        payment_pk = int(user_params['payment_pk'])
        payment = Payment.objects.get(pk = payment_pk)
        Sum = payment.amount
        Contract = '''
        <?xml version="1.0" encoding="utf-8"?>
            <contract>
                <param id="comment" ref="comment" label="Комментарий">%s</param>
                <param id="sum" ref="sum" label="Сумма">%s</param>
            </contract>
        '''%(payment.comment, payment.amount)
        PayeeRegData = "%s"%payment_pk
        PaymentDelay = 0
        return PayeeRegData, Sum, Contract, PaymentDelay

    @rpc(String, String, DateTime,Integer,Float,Boolean, _returns=(String, Boolean), _out_variable_names=('ReplyResourse', 'ReplyResourceIsFailure'))
    def PaymentAuthorization(ctx, PaymentID, PayeeRegData,  PaymentTime, Currency, Sum, IsRepeat):
        payment_pk = int(PayeeRegData)
        payment = Payment.objects.get(pk = payment_pk)
        if Sum == payment.amount:
            payment.status = Payment.STATUS_SUCCESS
        payment.save()
        #TODO:уточнить формат ответа
        ReplyResourse = '''
        <?xml version="1.0" encoding="utf-8"?>
            <contract>
                <param id="comment" ref="comment" label="Комментарий">%s</param>
                <param id="sum" ref="sum" label="Сумма">%s</param>
            </contract>
        '''%(payment.comment, payment.amount)
        ReplyResourceIsFailure = False
        return ReplyResourse, ReplyResourceIsFailure

    @rpc(String, DateTime, Integer,String,String)
    def PaymentCancellatuon(ctx, PaymentID, PaymentTime,  PaymentResult, PaymentResultStr, PayeeRegData):
        payment_pk = int(PayeeRegData)
        payment = Payment.objects.get(pk = payment_pk)
        payment.status = Payment.STATUS_FAILED
        payment.status = PaymentResultStr
        payment.save()


mobi_money_service = csrf_exempt(DjangoApplication(Application([MobiMoneyService],
   'urn:PaycashShopService',
    interface=Wsdl11(),
    in_protocol=Soap11(),
    out_protocol=Soap11()
)))