# -*- coding: utf-8 -*-
from urlparse import parse_qs
from django.http import HttpResponse
from cashflow.models import Payment
from rpclib.server.django import DjangoApplication
from rpclib.model.primitive import String, Integer, DateTime
from rpclib.model.complex import  ComplexModel
from rpclib.service import ServiceBase
from rpclib.interface.wsdl import Wsdl11
from rpclib.protocol.soap import Soap11
from rpclib.application import Application
from rpclib.decorator import rpc
from django.views.decorators.csrf import csrf_exempt


class PaymentContract(ComplexModel):
    __namespace__ = __name__
    Sum = Integer
    Contract = String
    PayeeRegData = String
    PaymentDelay = Integer


class MobiMoneyService(ServiceBase):
    @rpc(Integer, DateTime,String, _returns=PaymentContract)
    def payment_contract(ctx, PaymentID, PaymentTime, UserParams):
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
        return PaymentContract(Sum = Sum, Contract = Contract, PayeeRegData=PayeeRegData, PaymentDelay=PaymentDelay)

        #    @rpc(Integer, DateTime,String, _returns=Array)
#    def payment_authorization(ctx, PaymentID, PaymentTime, UserParams):
#        return []
mobi_money_service = csrf_exempt(DjangoApplication(Application([MobiMoneyService],
    __name__,
    interface=Wsdl11(),
    in_protocol=Soap11(),
    out_protocol=Soap11()
)))