frappe.ui.form.on("Library Transaction", {
    refresh(frm) {
        // Prevent running on unsaved or non-Issue/non-Submitted docs
        if (frm.is_new() || frm.doc.docstatus !== 1 || frm.doc.type !== "Issue") return;

        frappe.call({
            method: "library_management.library_management_system.doctype.library_transaction.library_transaction.update_articles_button",
            args: { transaction: frm.doc.name },
            callback: (r) => {
                if (r.message === true) {
                    frm.add_custom_button(__("Update Articles"), () => {
                        open_article_dialog(frm);
                    });
                }
            }
        });
    }
});

function open_article_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Select New Articles'),
        fields: [
            {
                label: __('Articles'),
                fieldname: 'articles',
                fieldtype: 'MultiSelect',
                get_data: function() {
                    // This fetches available articles for the MultiSelect dropdown
                    return frappe.db.get_link_options('Article', '', { status: 'Available' });
                },
                reqd: 1
            }
        ],
        primary_action_label: __('Update'),
        primary_action(values) {
            // values.articles will be a comma-separated string from MultiSelect
            let article_list = values.articles.split(',').map(a => a.trim());

            frappe.call({
                method: "library_management.library_management_system.doctype.library_transaction.library_transaction.update_articles",
                args: {
                    docname: frm.doc.name,
                    articles: article_list
                },
                callback: (r) => {
                    if (r.message) {
                        d.hide();
                        frm.reload_doc();
                        frappe.show_alert({ message: __('Articles updated successfully'), indicator: 'green' });
                    }
                }
            });
        }
    });
    d.show();
}