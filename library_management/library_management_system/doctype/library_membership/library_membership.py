# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
from frappe.model.docstatus import DocStatus
from frappe.utils import add_days, today, date_diff,getdate
from frappe.utils.data import flt

class LibraryMembership(Document):
    def before_save(self):
        exists = frappe.db.exists(
            "Library Membership",
            {
                "member": self.member,
                "docstatus": 1,
                # check if the membership's end date is later than this membership's start date
                "to_date": (">", self.from_date),
            },
        )
        if exists:
            frappe.throw(f"There is an active membership for this member")

        # loan_period = frappe.db.get_single_value("Library Settings", "loan_period")
        # self.to_date = frappe.utils.add_days(self.from_date, loan_period or 30)

    def before_submit(self):
        self.check_penalty()
    
    def check_penalty(self):
        last_membership=frappe.db.get_value(
            "Library Membership",
            {"member": self.member, "docstatus": 1, "name":("!=", self.name)},
            ["name", "to_date"],
            order_by="to_date desc",
            as_dict=True,
        )

        if not last_membership or not last_membership.to_date:
            return
        
        check_days=add_days(last_membership.to_date,10)
        
        if getdate(self.from_date) <= getdate(check_days):
            return 
        
        penalty_days=date_diff(getdate(self.from_date),getdate(check_days))
        

        penalty_type=frappe.db.get_value(
            "Penalty Types",
            {"penalty_type": "Membership Penalty"},
            ["name", "penalty_per_day"],
            as_dict=True,
        )

        total_penalty=penalty_days*flt(penalty_type.penalty_per_day)

        existing_penalty=frappe.db.get_value(
            "Penalty",
            {
                "library_member": self.member,
                "penalty_type": penalty_type.name,
                "docstatus": ["<", 2],
            },
            ["name", "paid"],
            as_dict=True
        )
        if existing_penalty:
            if existing_penalty.paid==0:
                frappe.throw(f"There is an unpaid membership penalty of ₹{total_penalty} for this member.")
            else:
                return
            
        # unpaid_penalty=frappe.db.exists(
        #     "Penalty",
        #     {
        #         "library_member": self.member,
        #         "penalty_type": penalty_type.name,
        #         "paid": 0,
        #         "docstatus": 1,
        #     }
        # )
        
        # if unpaid_penalty:
        #     frappe.throw(f"There is an unpaid membership penalty {total_penalty} for this member.")
        
        new_penalty = frappe.new_doc("Penalty")
        new_penalty.library_member = self.member
        new_penalty.penalty_type = penalty_type.name
        new_penalty.penalty_amount = total_penalty
        new_penalty.paid = 0
        new_penalty.insert(ignore_permissions=True)

        frappe.db.commit()

        frappe.throw(
            f"Membership penalty of ₹{total_penalty} created. Please pay before submitting."
        )
