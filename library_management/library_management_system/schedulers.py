import frappe
from frappe.utils import nowdate

def notify_new_articles():
    today = nowdate()

    new_articles = frappe.db.get_all(
        "Article",
        filters={"creation": ("like", f"{today}%")},
        fields=["article_name", "total_quantity", "creation"]
    )

    if not new_articles:
        frappe.logger().info("No new articles added today")
        return

    # ✅ Change this email to your admin/librarian email
    admin_email = "ajishbenz@gmail.com"

    article_list = ""
    for a in new_articles:
        article_list += f"- {a.article_name} ({a.total_quantity})<br>"

    frappe.sendmail(
        recipients=[admin_email],
        subject=f"📚 New Articles Added Today ({len(new_articles)})",
        message=f"""
            Hello Admin,<br><br>
            New articles added today ({today}):<br><br>
            {article_list}<br><br>
            Thanks.
        """
    )

    frappe.logger().info(f"Reminder sent for {len(new_articles)} new articles")

def update_member_active_status():
    today = nowdate()

    # 1) Make all members inactive
    frappe.db.sql("""UPDATE `tabLibrary Member` SET active = 0""")

    # 2) Get members who have active membership today
    active_members = frappe.get_all(
        "Library Membership",
        filters={
            "docstatus": 1,
            "from_date": ["<=", today],
            "to_date": [">=", today]
        },
        pluck="member"
    )

    # 3) Tick active for valid members
    for member_id in set(active_members):
        frappe.db.set_value("Library Member", member_id, "active", 1, update_modified=False)

    frappe.db.commit()