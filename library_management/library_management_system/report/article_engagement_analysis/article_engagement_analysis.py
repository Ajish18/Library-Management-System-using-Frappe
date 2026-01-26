# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.test_search import get_data


def execute(filters=None):
	columns= get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
    return [
        {
            "label": "Library Member",
            "fieldname": "library_member",
            "fieldtype": "Link",
            "options": "Library Member",
            "width": 150
        },
        {
            "label": "Article",
            "fieldname": "article",
            "fieldtype": "Link",
            "options": "Article",
            "width": 200
        },
        {
            "label": "Access Count",
            "fieldname": "access_count",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": "Total Quantity",
            "fieldname": "total_quantity",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": "Engagement Level",
            "fieldname": "engagement_level",
            "fieldtype": "Data",
            "width": 150
        }
    ]


def get_data(filters):
    rows = frappe.db.sql("""
        SELECT
            lt.library_member as library_member,
            lt.article as article,
            COUNT(*) as access_count,
            a.total_quantity as total_quantity
        FROM `tabLibrary Transaction` lt
        LEFT JOIN `tabArticle` a ON a.name = lt.article
        WHERE lt.type = 'Issue' and lt.docstatus = 1
        GROUP BY lt.library_member, lt.article
        ORDER BY access_count DESC
    """, as_dict=True)


    for r in rows:
        access = r.get("access_count") or 0
        qty = r.get("total_quantity") or 0

        if qty > 0 and access >= (qty / 2):
            r["engagement_level"] = "High"
        elif access == (qty / 2):
            r["engagement_level"] = "Medium"
        else:
            r["engagement_level"] = "Low"

    return rows