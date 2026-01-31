# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt

from annotated_types import doc
import frappe
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, getdate, today
from frappe.utils.data import flt

class LibraryTransaction(Document): 
    
    def before_submit(self):
        self.validate_member_active()
        if(self.type=="Issue"):
            self.count=len(self.article)
            self.validate_max_article_limit()
            self.validate_penalty_available()
            self.article_exists()
            self.validate_issue()
        elif(self.type=="Return"):
            self.validate_return()

    def before_save(self):
        if self.type=="Issue":
            loan_period = frappe.db.get_single_value("Library Settings", "loan_period")
            self.return_date = frappe.utils.add_days(self.date, loan_period or 10)

    def on_submit(self):
        member_details=frappe.db.get_value("Library Member",self.library_member,
        ["issued_count","books_issued"],as_dict=True)
        issued_count=member_details.issued_count or 0
        article_issued=member_details.books_issued or 0
        if self.type == "Issue":
            self.update_issue()
            issued_count += self.count
            article_issued = 1
        elif self.type == "Return":
            self.check_penalty()
            self.update_return()
            issued_count -= len(self.article)
            if issued_count <= 0:
                article_issued = 0
        frappe.db.set_value("Library Member", self.library_member, {
            "issued_count": issued_count,
            "article_issued": article_issued
        }
        )
        
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
        existing_articles=self.article_exists()
        for row in self.article:
            if row.article in existing_articles:
                frappe.throw(f"Article {row.article} is already issued to this member.")

            if row.article in issued_articles:
                frappe.throw(f"Article {row.article} is duplicated in the transaction.")
            issued_articles.add(row.article)
            article_status=frappe.db.get_value("Article",
            row.article, ["available_quantity"], as_dict=True)
            if(article_status.available_quantity<1):
                frappe.throw(f"Article {row.article} is not available for issue.")

    
    def article_exists(self):
        existing_articles=[]
        member=frappe.get_doc("Library Member",self.library_member)
        for row in member.articles_issued:
            existing_articles.append(row.article_issued)
        return existing_articles

    def update_issue(self):
        for row in self.article:
            article=frappe.db.set_value("Article",row.article, {
                "available_quantity": frappe.db.get_value("Article", row.article, "available_quantity") - 1,
                "issued_quantity": frappe.db.get_value("Article", row.article, "issued_quantity") + 1
            })
            doc = frappe.get_doc({
                "doctype": "Issued Articles",
                "parent": self.library_member,
                "parenttype": "Library Member",
                "parentfield": "articles_issued",
                "article_issued": row.article,
                "transaction_reference": self.name
            })

            doc.insert(ignore_permissions=True)
            


    def validate_return(self):
        existing_articles=self.article_exists()
        for row in self.article:
            if row.article not in existing_articles:
                frappe.throw(f"Article {row.article} is not issued to this member.")
        
    
    def update_return(self):
        for row in self.article:
            article = frappe.db.get_value("Article", row.article, ["available_quantity", "issued_quantity"], as_dict=True)

            frappe.db.set_value("Article", row.article, {
                "available_quantity": article.available_quantity + 1,
                "issued_quantity": article.issued_quantity - 1,
                "status": "Available"
            })
            frappe.db.delete("Issued Articles", {
                "parent": self.library_member,
                "parenttype": "Library Member",
                "parentfield": "articles_issued",
                "article_issued": row.article
            })

    def validate_max_article_limit(self):
        curr_count=frappe.db.count(
            "Issued Articles",
            {
                "parent": self.library_member,
                "parenttype": "Library Member",
                "parentfield": "articles_issued",
            }
        )
        limit=frappe.db.get_single_value("Library Settings","max_articles_per_person")or 5

        if(curr_count + self.count > limit):
            frappe.throw(f"You cannot issue more than {limit} articles.You can issue only{limit-curr_count} articles.")


    def check_penalty(self):
        penalty_amount=0
        for row in self.article:
            issued_id=frappe.db.get_value(
                "Issued Articles",
                {
                "parent": self.library_member,
                "article_issued": row.article
                },
                "transaction_reference"
            )
                
            return_date=frappe.db.get_value("Library Transaction", issued_id, "return_date")
            if(getdate(self.date)>getdate(return_date)):
                overdue=date_diff(getdate(self.date),getdate(return_date))
                penalty_amount+=self.generate_amount(overdue)
        if(penalty_amount>0):
            self.generate_penalty(penalty_amount)
    
    def generate_amount(self, overdue):
        penalty_type=frappe.db.get_value(
            "Penalty Types",
            {"penalty_type": "Book Overdue"},
            ["penalty_per_day"],
            as_dict=True,
        )
        amount=overdue*penalty_type.penalty_per_day
        return amount
    
    def generate_penalty(self, penalty_amount):
        penalty_type=frappe.db.get_value(
            "Penalty Types",
            {"penalty_type": "Book Overdue"},
            ["penalty_per_day"],
            as_dict=True,
        )
        frappe.get_doc({
            "doctype": "Penalty",
            "library_member": self.library_member,
            "penalty_type": penalty_type.name,
            "penalty_amount": penalty_amount,
            "transaction_reference": self.name,
            "paid": 0,
            }).insert(ignore_permissions=True)

        frappe.msgprint(
        f"Late return detected. Penalty of ₹{penalty_amount} has been generated.",
        indicator="orange",
        alert=True,)

        frappe.msgprint(f"Penalty amount of rs.{penalty_amount} is available.")
    

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
    


# @frappe.whitelist()
# def update_articles_button(transaction):
#     transaction = frappe.get_doc("Library Transaction", transaction)
#     if transaction.docstatus!=1 or transaction.type!="Issue":
#         frappe.throw("Only submitted Issue transactions can be updated.")
    
#     issued_count=frappe.db.get_value(
#         "Library Member",
#         transaction.library_member,
#         "issued_count"
#     ) or 0

#     return issued_count==transaction.count
    
# @frappe.whitelist()
# def update_articles(docname,articles):
#     doc=frappe.get_doc("Library Transaction", docname)
#     issued_count=frappe.db.get_value(
#         "Library Member",
#         doc.library_member,
#         "issued_count"
#     ) or 0

#     if(issued_count!=doc.count):
#         frappe.throw("You cannot update articles as you have already returned some articles.")

#     doc.set("articles",[])
#     for article in articles:
#         doc.append("articles",{
#             "article":article
#         })
#     doc.count=len(articles)
#     doc.save(ignore_permissions=True)
#     frappe.db.commit()

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

