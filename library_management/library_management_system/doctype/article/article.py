# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Article(Document):
	# def get_issued_count(self):
	# 	return frappe.db.count(
    #         "Library Transaction",
    #         {
    #             "article": self.name,
    #             "type": "Issue",
    #             "docstatus": 1
    #         }
    #     )
	def recalculate_available_qty(self):
		old_total = self.issued_quantity + self.available_quantity
		new_qty = self.total_quantity - old_total
		self.available_quantity += new_qty
		if self.available_quantity == 0:
			self.status = "Issued"

		else:
			self.status = "Available"

	def before_insert(self):
		if not self.issued_quantity:
			self.issued_quantity = 0
	
		self.available_quantity = self.total_quantity
		self.status = "Available"
		
	def on_update(self):
		self.recalculate_available_qty()