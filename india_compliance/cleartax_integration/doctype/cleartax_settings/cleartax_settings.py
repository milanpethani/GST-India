# Copyright (c) 2022, Resilient Tech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from india_compliance.cleartax_integration.API.gst import bulk_purchase_gst, create_gst_invoice


class CleartaxSettings(Document):
	def tax_id(self,gstin):
		return frappe.get_value('Tax Entities',{'gstin':gstin,'parent':self.name},'entity_id')


@frappe.whitelist()
def irn_failed():
    sql  = """
                    SELECT 
                        COUNT(*) as count
                    FROM `tabSales Invoice` as si
                    LEFT JOIN `tabCleartax Api Log` as al ON si.name = al.document_name
                    AND al.api = 'GENERATE IRN'
					AND al.status = 'Failed'
                """ 
    return frappe.db.sql(sql,as_dict=1)[0]['count']


@frappe.whitelist()
def ewb_irn_failed():
    sql  = """
                    SELECT 
                        COUNT(*) as count
                    FROM `tabSales Invoice` as si
                    LEFT JOIN `tabCleartax Api Log` as al ON si.name = al.document_name
                    AND al.api = 'GENERATE EWB BY IRN'
					AND al.status = 'Failed'
                """ 
    return frappe.db.sql(sql,as_dict=1)[0]['count']

@frappe.whitelist()
def ewb_failed():
    sql  = """
                    SELECT 
                        COUNT(*) as count
                    FROM `tabDelivery Note` as si
                    LEFT JOIN `tabCleartax Api Log` as al ON si.name = al.document_name
                    AND al.api = 'GENERATE EWB WITHOUT IRN'
					AND al.status = 'Failed'
                """ 
    return frappe.db.sql(sql,as_dict=1)[0]['count']


def sales_gst_job(data):
    for i in data:
        create_gst_invoice(**{'invoice':i.name,'type':'SALE'})

def purchase_gst_job(data):
    for i in data:
        create_gst_invoice(**{'invoice':i.name,'type':'PURCHASE'})


@frappe.whitelist()
def push_to_cleartax(**kwargs):
    if kwargs.get('sales_invoice'):
        sales_invoices = """
                            SELECT 
                                inv.name as name
                            FROM
                                `tabSales Invoice` as inv
                            WHERE name NOT IN
                                (SELECT log.document_name as name
                                FROM
                                    `tabCleartax Api Log` as log)
                            AND
                                inv.irn IS NOT NULL
                            AND inv.creation >= '%s'
                            AND inv.docstatus = 1
                            """ %(kwargs.get('sales_invoice'))
        sales_invoices = frappe.db.sql(sales_invoices,as_dict=1)
        frappe.enqueue(sales_gst_job, data=sales_invoices, queue='long')
    if kwargs.get('purchase_invoice'):
        purchase_invoices = frappe.get_all("Purchase Invoice",filters=[['docstatus','=',1],['creation','>=',kwargs.get('purchase_invoice')]])
        frappe.enqueue(purchase_gst_job, data=purchase_invoices, queue='long')
@frappe.whitelist()
def push_to_gst():
    sales_invoices = """
                            SELECT 
                                inv.name as name
                            FROM
                                `tabSales Invoice` as inv
                            WHERE name IN
                                (SELECT log.document_name as name
                                FROM
                                    `tabCleartax Api Log` as log)
                            AND
                                inv.irn IS NOT NULL
                            AND inv.docstatus = 1
                            """
    sales_invoices = frappe.db.sql(sales_invoices,as_dict=1)
    for i in sales_invoices:
        frappe.enqueue("india_compliance.cleartax_integration.API.gst.create_gst_invoice",**{'invoice':i.name,'type':'SALE'})

@frappe.whitelist()
def retry_failed_pi():
    pi_list = frappe.get_all('Cleartax APi Log',filters=[['api','in',['GENERATE GST PINV','GENERATE GST CDN']],['status','Failed']],fields=['document_name'])
    for i in pi_list:
            frappe.enqueue("india_compliance.cleartax_integration.API.gst.create_gst_invoice",**{'invoice':i.document_name,'type':'PURCHASE'})


@frappe.whitelist()
def retry_faield_si():
    si_list = frappe.get_all('Cleartax APi Log',filters=[['api','in',['GENERATE GST SINV','GENERATE GST CDN']],['status','Failed']],fields=['document_name'])
    for i in si_list:
            frappe.enqueue("india_compliance.cleartax_integration.API.gst.create_gst_invoice",**{'invoice':i.document_name,'type':'SALE'})



@frappe.whitelist()
def push_pi_gst():
    purchase_invoices = frappe.get_all('Purchase Invoice',{'gst_invoice':1})
    for i in purchase_invoices:
            frappe.enqueue("india_compliance.cleartax_integration.API.gst.create_gst_invoice",**{'invoice':i.name,'type':'PURCHASE'})