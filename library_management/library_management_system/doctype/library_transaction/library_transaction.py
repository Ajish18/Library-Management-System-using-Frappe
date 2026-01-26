# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
# from frappe.model.docstatus import DocStatus

class LibraryTransaction(Document):
    def before_submit(self):
        self.validate_member_active()
        if(self.type=="Issue"):
            self.validate_issue()
        else:
            self.validate_return()
    
    def validate_member_active(self):
        mem_status=frappe.db.get_value("Library Member",self.library_member,"active")
        trans_type=self.type
        vaild_member=frappe.db.exists(
            "Library Membership",
            {
                "member": self.library_member,
                "docstatus": 1,
                "from_date": ("<=", self.date),
                "to_date": (">=", self.date),
            }
        )
        if not vaild_member:
            frappe.throw("The library member is not active on the transaction date.")

        if (mem_status==0 and trans_type=="Issue"):
            frappe.throw("The library member is inactive and cannot issue articles.")

    
    
    def validate_issue(self):
        
        for row in self.article:
            article_status = frappe.get_doc("Article", row.article)
            avail_qty=(article_status.available_quantity)
            if(avail_qty<row.quantity):
                frappe.throw(f"Article {row.article} is not available for issue.")
            else:
                article_status.available_quantity -= row.quantity
                article_status.issued_quantity += row.quantity
                if(article_status.available_quantity==0):
                    article_status.status="Issued"
                article_status.save()

    def validate_return(self):
        for row in self.article:
            article_status = frappe.get_doc("Article", row.article)
            issued_qty=(article_status.issued_quantity)
            if(issued_qty<row.quantity):
                frappe.throw(f"Return quantity for Article {row.article} exceeds issued quantity.")
            else:
                article_status.available_quantity += row.quantity
                article_status.issued_quantity -= row.quantity
                if(article_status.available_quantity>0):
                    article_status.status="Available"
                article_status.save()

    def on_cancel(self):
        for row in self.article:
            article_status = frappe.db.get_doc("Article", row.article)
            if(self.type=="Issue"):
                article_status.available_quantity += row.quantity
                article_status.issued_quantity -= row.quantity
                if(article_status.available_quantity>0):
                    article_status.status="Available"
            else:
                article_status.available_quantity -= row.quantity
                article_status.issued_quantity += row.quantity
                if(article_status.available_quantity==0):
                    article_status.status="Issued"
            article_status.save()