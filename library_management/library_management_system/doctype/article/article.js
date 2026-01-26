// Copyright (c) 2026, Ajish and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Article", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Article', {
    total_quantity(frm) {
        if (frm.is_new()) {
            frm.set_value('available_quantity', frm.doc.total_quantity);
        }
    }
});
