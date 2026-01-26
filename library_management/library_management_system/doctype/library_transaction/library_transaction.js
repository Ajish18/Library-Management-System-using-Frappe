frappe.ui.form.on("Library Transaction", {
    refresh(frm) {
        frm.trigger("set_article_filter");
    },

    type(frm) {
        frm.trigger("set_article_filter");
        frm.refresh_field("article");
    },

    set_article_filter(frm) {
        frm.fields_dict["article"].grid.get_field("article").get_query = function (doc, cdt, cdn) {
            if (frm.doc.type === "Issue") {
                return {
                    filters: {
                        status: "Available"
                    }
                };
            }
            return {};
        };
    },

    async validate(frm) {
        // apply only when Issue
        if (frm.doc.type !== "Issue") return;

        for (let row of (frm.doc.article || [])) {
            if (!row.article || !row.quantity) continue;

            let r = await frappe.db.get_value("Article", row.article, "available_quantity");
            let available = r.message.available_quantity || 0;

            if (row.quantity > available) {
                frappe.throw(
                    `Row ${row.idx}: You entered ${row.quantity} but only ${available} available for Article ${row.article}`
                );
            }
        }
    }

});

