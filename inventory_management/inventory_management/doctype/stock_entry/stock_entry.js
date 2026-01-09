// Copyright (c) 2026, Krishna and contributors
// For license information, please see license.txt

function set_warehouse_df_property(frm){
    if(frm.doc.transaction_type == "Receipt"){
        frm.set_df_property("from_warehouse","hidden",1);
        frm.set_df_property("to_warehouse","hidden",0);
        frm.set_df_property('from_warehouse', 'reqd', false);  
        frm.set_df_property('to_warehouse', 'reqd', true); 
        frm.set_value('from_warehouse', null);  
    }
    else if(frm.doc.transaction_type == "Consume"){
        frm.set_df_property("from_warehouse","hidden",0);
        frm.set_df_property("to_warehouse","hidden",1);
        frm.set_df_property('from_warehouse', 'reqd', true);  
        frm.set_df_property('to_warehouse', 'reqd', false);  
        frm.set_value('to_warehouse', null);  
    }
    else if(frm.doc.transaction_type == "Transfer"){
        frm.set_df_property("from_warehouse","hidden",0);
        frm.set_df_property("to_warehouse","hidden",0);
        frm.set_df_property('from_warehouse', 'reqd', true);  
        frm.set_df_property('to_warehouse', 'reqd', true);  
    }
}

frappe.ui.form.on("Stock Entry", {
    onload(frm){
        frm.set_df_property('from_warehouse', 'reqd', true);  
        frm.set_df_property('to_warehouse', 'reqd', true);  
        set_warehouse_df_property(frm);
    },
    transaction_type(frm){
        set_warehouse_df_property(frm);
    }
});


