// frappe.ui.form.on("Library Transaction", {
//     refresh(frm) {
//         if (frm.is_new()) return;

//         if(frm.doc.docstatus !== 1 && frm.doc.type !== "Issue") return;
//         frappe.call({
//             method:"library_management.library_management_system.doctype.library_transaction.library_transaction.update_articles_button",
//             args:{
//                 transaction: frm.doc.name
//             },
//             callback(r){
//                 if(r.message===true){
//                     frm.add_custom_button("Update Articles", ()=>{
//                         open_article_dialog(frm);
//                     })
//             }
//         }
//         });

//         // frm.trigger("set_article_filter");
//     },

//     // type(frm) {
//     //     frm.trigger("set_article_filter");
//     //     frm.refresh_field("article");
//     // },

//     // set_article_filter(frm) {
//     //     frm.fields_dict["article"].grid.get_field("article").get_query = function (doc, cdt, cdn) {
//     //         if (frm.doc.type === "Issue") {
//     //             return {
//     //                 filters: {
//     //                     status: "Available"
//     //                 }
//     //             };
//     //         }
//     //         return {};
//     //     }; 
//     // },


// });

