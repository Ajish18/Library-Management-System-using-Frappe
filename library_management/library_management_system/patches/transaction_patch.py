import frappe

def execute():
    old_transactions = frappe.db.get_all(
        "Library Transaction",
        fields=["name", "old_article"],
        filters={"old_article": ["!=", ""]}
    )

    for lt in old_transactions:
        # Skip if child row already exists
        if frappe.db.exists(
            "Article selection",
            {
                "parent": lt.name,
                "parenttype": "Library Transaction",
                "parentfield": "article"
            }
        ):
            continue

        # Insert child row
        frappe.get_doc({
            "doctype": "Article selection",
            "parent": lt.name,
            "parenttype": "Library Transaction",
            "parentfield": "article",
            "article": lt.old_article,
            "quantity": 1
        }).insert(ignore_permissions=True)
    frappe.db.commit()