// Copyright (c) 2026, Krishna and contributors
// For license information, please see license.txt

frappe.ui.form.on("Stock Entry", {
    transaction_type(frm){
        // frm.set_intro('Please set the value of description', 'blue');
        if(frm.doc.transaction_type == "Receipt"){
            frm.set_df_property("from_warehouse","hidden",1);
            frm.set_df_property("to_warehouse","hidden",0);
        }
        else if(frm.doc.transaction_type == "Consume"){
            frm.set_df_property("from_warehouse","hidden",0);
            frm.set_df_property("to_warehouse","hidden",1);
        }
        else if(frm.doc.transaction_type == "Transfer"){
            frm.set_df_property("from_warehouse","hidden",0);
            frm.set_df_property("to_warehouse","hidden",0);
        }

    },
    item_list_add(frm, cdt, cdn) { 

        frappe.msgprint('A row has been added to the links table 🎉 ');
    },
	// refresh(frm) {
        
	// },
});
