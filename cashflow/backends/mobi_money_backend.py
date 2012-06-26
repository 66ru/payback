# -*- coding: utf-8 -*-
from urlparse import parse_qs
from django.core.exceptions import ObjectDoesNotExist
from cashflow.models import Payment, ClientBackend
from rpclib.model.fault import Fault
from rpclib.server.django import DjangoApplication
from rpclib.model.primitive import String, Integer, DateTime, Float, Boolean
from rpclib.service import ServiceBase
from rpclib.interface.wsdl import Wsdl11
from rpclib.protocol.soap import Soap11
from rpclib.application import Application
from rpclib.decorator import rpc
from django.views.decorators.csrf import csrf_exempt
from cashflow.backends.common import ReturnedTextException

class MobiMoneyService(ServiceBase):
    @rpc(String, DateTime,String, Boolean, _returns=(String, Float, String, Integer), _out_variable_names=('PayeeRegData', 'Sum', 'Contract', 'PaymentDelay'))
    def PaymentContract(ctx, PaymentID, PaymentTime, UserParams, Demo):
        user_params = parse_qs(UserParams)
        payment_pk = int(user_params['payment_pk'])
        try:
            payment = Payment.objects.get(pk = payment_pk)
        except ObjectDoesNotExist:
            raise Fault(faultcode='incorrect_request', faultstring='Неверный номер заказа')
        if payment.status == Payment.STATUS_SUCCESS:
            raise Fault(faultcode='already_paid')

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
        else:
            raise Fault(faultcode='error', faultstring='Сумма платежа не совпадает')
        payment.save()
        #TODO:уточнить формат ответа
        ReplyResourse = '''
        <?xml version="1.0" encoding="utf-8"?>
            <contract>
                <param id="order" ref="order" label="Номер заказа">%s</param>
                <param id="sum" ref="sum" label="Сумма">%s</param>
            </contract>
        '''%(payment.pk, payment.amount)
        ReplyResourceIsFailure = False
        return ReplyResourse, ReplyResourceIsFailure

    @rpc(String, DateTime, Integer,String,String)
    def PaymentCancellation(ctx, PaymentID, PaymentTime,  PaymentResult, PaymentResultStr, PayeeRegData):
        payment_pk = int(PayeeRegData)
        try:
            payment = Payment.objects.get(pk = payment_pk)
        except ObjectDoesNotExist:
            raise Fault(faultcode='error', faultstring='Заказа с таким номером нет')
        payment.status = Payment.STATUS_FAILED
        payment.status = PaymentResultStr
        payment.save()


mobi_money_service = csrf_exempt(DjangoApplication(Application([MobiMoneyService],
   'urn:PaycashShopService',
    interface=Wsdl11(),
    in_protocol=Soap11(),
    out_protocol=Soap11(),
    name='PaybackMobiMoney'
)))

def send_payment(payment):
    client_backend = ClientBackend.objects.get(client = payment.client, backend=payment.backend)
    cp = client_backend.get_config_parser()

    sms_text_raw = cp.get('mobi_money', 'sms_text')
    number = cp.get('mobi_money', 'number')
    sms_text = sms_text_raw%({'sum':payment.amount, 'order':payment.pk})


    raise ReturnedTextException(text= sms_text, message='(sms text): %s'%sms_text, number=number)