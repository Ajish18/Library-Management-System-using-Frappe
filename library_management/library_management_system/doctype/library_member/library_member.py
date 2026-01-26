# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class LibraryMember(Document):
    def before_save(self):
        self.full_name = f'{self.f_name} {self.l_name or ""}'
