// Copyright (c) 2026, Ajish and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Library Membership", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on("Library Membership", {
    membership_plan(frm) {
        frm.trigger("set_to_date");
    },

    from_date(frm) {
        frm.trigger("set_to_date");
    },

    set_to_date(frm) {
        if (!frm.doc.from_date || !frm.doc.membership_plan) return;

        frappe.db.get_value(
            "Membership Plans",
            frm.doc.membership_plan,
            "membership_periodin_days",
            function(res) {
                let days = res.membership_periodin_days;
                let to_date = frappe.datetime.add_days(frm.doc.from_date, days);
                frm.set_value("to_date", to_date);
            }
            );
    }
});




