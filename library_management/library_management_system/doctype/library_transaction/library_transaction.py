# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt

from enum import member
from annotated_types import doc
import frappe
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, getdate, today
from frappe.utils.data import flt
# from frappe.model.docstatus import DocStatus

class LibraryTransaction(Document):
    def before_submit(self):
        #self.check_penalty()
        self.validate_member_active()
        if(self.type=="Issue"):
            self.validate_penalty_available()
            self.validate_article_issued()
            self.validate_issue()
            self.count=len(self.article)
        elif(self.type=="Return"):
            self.validate_return()
            self.count=len(self.article)

    def before_save(self):
        if self.type=="Issue":
            loan_period = frappe.db.get_single_value("Library Settings", "loan_period")
            self.return_date = frappe.utils.add_days(self.date, loan_period or 10)

    def on_submit(self):
        member = frappe.get_doc("Library Member", self.library_member)
        if self.type == "Issue":
            self.update_issue()
            member.issued_count += self.count
            member.books_issued = 1
        elif self.type == "Return":
            self.check_penalty()
            self.update_return()
            member.issued_count -= self.count
            if member.issued_count <= 0:
                member.issued_count = 0
                member.books_issued = 0

        member.save(ignore_permissions=True)
        
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
        issued_articles=set()
        for row in self.article:
            if row.article in issued_articles:
                frappe.throw(f"Article {row.article} is duplicated in the transaction.")
            issued_articles.add(row.article)
            article_status=frappe.get_doc("Article", row.article)
            if(article_status.available_quantity<1):
                frappe.throw(f"Article {row.article} is not available for issue.")


    def update_issue(self):
        for row in self.article:
            article=frappe.get_doc("Article",row.article)
            article.available_quantity -= 1
            article.issued_quantity += 1
            if(article.available_quantity==0):
                article.status="Issued"
            article.save()
        


    def validate_return(self):
        for row in self.article:
            article = frappe.get_doc("Article", row.article)
            if article.issued_quantity < 1:
                frappe.throw(f"Article {article.name} was not issued to this member.")
        
        
    
    def update_return(self):
        for row in self.article:
            article = frappe.get_doc("Article", row.article)

            article.available_quantity += 1
            article.issued_quantity -= 1
            article.status = "Available"
            article.save(ignore_permissions=True)

    # def on_cancel(self):
    #     member = frappe.get_doc("Library Member", self.library_member)
    #     for row in self.article:
    #         article_status = frappe.get_doc("Article", row.article)
    #         if(self.type=="Issue"):
    #             article_status.available_quantity += 1
    #             article_status.issued_quantity -= 1
    #             member.issued_count -= 1
    #             if(article_status.available_quantity>0):
    #                 article_status.status="Available"
    #         else:
    #             article_status.available_quantity -= 1
    #             article_status.issued_quantity += 1
    #             member.issued_count += 1
    #             if(article_status.available_quantity==0):
    #                 article_status.status="Issued"
    #         article_status.save()

    def validate_article_issued(self):
        member = frappe.get_doc("Library Member", self.library_member)

        if member.issued_count>0:
            frappe.throw(
                "You already have issued books. Please return them before issuing again."
            )
        


    def check_penalty(self):
        # 1. Get the Issue record that corresponds to this return
        issue_transaction = frappe.db.get_value(
            "Library Transaction",
            {"library_member": self.library_member, "type": "Issue", "docstatus": 1},
            ["name", "return_date"],
            order_by="creation desc",
            as_dict=True,
        )

        if not issue_transaction or not issue_transaction.return_date:
            return

        # 2. Calculate overdue days
        check_days = date_diff(getdate(self.date), getdate(issue_transaction.return_date))
        if check_days <= 0:
            return
        
        penalty_type = frappe.db.get_value(
            "Penalty Types", 
            {"penalty_type": "Book Overdue"}, 
            ["name", "penalty_per_day"], 
            as_dict=True,
        )
        
        tot_penalty = check_days * penalty_type.penalty_per_day * self.count

        frappe.get_doc({
            "doctype": "Penalty",
            "library_member": self.library_member,
            "penalty_type": penalty_type.name,
            "penalty_amount": tot_penalty,
            "transaction_reference": self.name,
            "paid": 0,
            }).insert(ignore_permissions=True)

        frappe.msgprint(
        f"Late return detected. Penalty of ₹{tot_penalty} has been generated.",
        indicator="orange",
        alert=True,)

        frappe.msgprint(f"Penalty amount of rs.{tot_penalty} is available.")
    

    def validate_penalty_available(self):
        unpaid_penalty = frappe.db.exists(
            "Penalty",
            {
                "library_member": self.library_member,
                "paid": 0,
                "docstatus": ["<", 2],
            }
        )

        if unpaid_penalty:
            frappe.throw(
                "You have unpaid penalties. Please clear them before issuing books."
            )
    
    @frappe.whitelist()
    def update_articles(transaction):
        transaction = frappe.get_doc("Library Transaction", transaction)
        if doc.status!=1 or doc.status!="Issue":
            frappe.throw("Only submitted Issue transactions can be updated.")
        
        issued_count=frappe.db.get_value(
            "Library Member",
            doc.library_member,
            "issued_count"
        ) or 0

        return issued_count==doc.count

