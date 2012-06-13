# -*- coding: utf-8 -*-
import json
from django.http import HttpResponse
from lxml import etree
from urlparse import parse_qs
from cashflow.models import Payment

test_xml = '''
<?xml version="1.0" encoding="utf-8"?>
<contract>
<param id="sum" label="Сумма, к зачислению на лицевой счёт">100</param>
<param id="account" label="Номер лицевого счёта">234523453453</param>
</contract>
'''
def _xml_params(xml):
    parser = etree.XMLParser(ns_clean=True,recover=True,encoding='utf-8')
    parsed_xml = etree.fromstring(xml, parser=parser)
    attrs_dict = dict()
    for action, param in etree.iterwalk(parsed_xml, tag="param"):
        id = param.attrib.pop('id')
        attrs_dict[id] = param.attrib
        attrs_dict[id]['text'] = param.text

        return attrs_dict

def payment_contract(request=test_xml):
    attrs_dict = _xml_params(request)

    try:
        payment_pk = parse_qs(attrs_dict['UserParams'])['payment_pk']
    except KeyError:
        error = etree.Element('error')
        param_id = etree.SubElement(error, 'param', id='errorCode', label=u'Код ошибки')
        param_id.text = 'incorrect_request'
        param_descr = etree.SubElement(error, 'param', id='errorDescr', label = u'Описание')
        param_descr.text = u'Некорректный запрос'
        return HttpResponse(etree.tostring(error, xml_declaration=True, encoding='utf-8'), mimetype='application/xml')

    payment = Payment.objects.get(pk = int(payment_pk))
    sum = payment.amount
    pay_reg_data =json.dumps({'payment_pk':payment_pk})
    contract = etree.Element('contract')
    param_sum = etree.SubElement(contract, 'param', id='Sum', label='Сумма')
    param_sum.text = sum
    param_reg_data = etree.SubElement(contract, 'param', id='PayeeRegData')
    param_reg_data.text = pay_reg_data
    return HttpResponse(etree.tostring(contract, xml_declaration=True, encoding='utf-8'), mimetype='application/xml')

def payment_authorization(request):
    attrs_dict = _xml_params(request)
    payment_pk = json.loads(attrs_dict['PayeeRegData'])['payment_pk']
    payment = Payment.objects.get(pk = int(payment_pk))

    payment.status = payment.STATUS_SUCCESS

    success = etree.Element('success')
    param_sum = etree.SubElement(success, 'param', id='sum', label=u'Сумма')
    param_sum.text = payment.sum
    return HttpResponse(etree.tostring(success, xml_declaration=True, encoding='utf-8'), mimetype='application/xml')