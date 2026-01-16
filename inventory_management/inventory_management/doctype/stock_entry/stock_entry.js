// Copyright (c) 2026, Krishna and contributors
// For license information, please see license.txt

function set_warehouse_df_property(frm){
    // Toggle child-table `from_warehouse` / `to_warehouse` column visibility/requirement
    const field = frm.fields_dict.item_list;
    if (!field || !field.grid) return;
    const grid = field.grid;
    const child_doctype = grid.doctype; // usually 'Items'

    // helper to show/hide column, set reqd/read_only on child df and clear values when hidden
    const setCol = (colname, show, reqd, editable) => {
        if (typeof grid.toggle_display === 'function') {
            grid.toggle_display(colname, show);
        }
        const df = frappe.meta.get_docfield(child_doctype, colname, frm.doc.doctype);
        if (df) {
            df.reqd = reqd ? 1 : 0;
            df.read_only = editable ? 0 : 1;
        }

        // If column not shown or not editable, clear values from existing rows
        if (!show || !editable) {
            const rows = frm.doc.item_list || [];
            rows.forEach(row => {
                try {
                    frappe.model.set_value(row.doctype, row.name, colname, null);
                } catch (e) {
                    // ignore failures
                }
            });
            // refresh so cleared values reflect immediately
            try { frm.refresh_field('item_list'); } catch (e) {}
        }
    };

    if (frm.doc.transaction_type == "Receipt"){
        // from_warehouse hidden, non-editable; to_warehouse visible and editable
        setCol('from_warehouse', false, false, false);
        setCol('to_warehouse', true, true, true);
    }
    else if (frm.doc.transaction_type == "Consume"){
        // from_warehouse visible and editable; to_warehouse hidden, non-editable
        setCol('from_warehouse', true, true, true);
        setCol('to_warehouse', false, false, false);
    }
    else if (frm.doc.transaction_type == "Transfer"){
        // both visible and editable
        setCol('from_warehouse', true, true, true);
        setCol('to_warehouse', true, true, true);
    }

    // refresh grid header to reflect df changes
    try {
        grid.refresh();
    } catch (e) {
        // best-effort: ignore refresh failures
        console.warn('grid refresh failed', e);
    }
}

frappe.ui.form.on("Stock Entry", {
    onload(frm){
        set_warehouse_df_property(frm);
    },
    transaction_type(frm){
        set_warehouse_df_property(frm);
        // Update existing rows' valuations according to new transaction type
        const rows = frm.doc.item_list || [];
        rows.forEach(r => {
            if (r && r.name) {
                // trigger a recalculation for each row
                frappe.events.trigger && frappe.events.trigger('recalculate_item_valuation');
                // call helper explicitly
                fetch_and_set_valuation(frm, r.doctype, r.name);
            }
        });
    }
});

// Helper: fetch latest MA valuation for product+warehouse and set `valuation` on the row
function fetch_and_set_valuation(frm, cdt, cdn) {
    const row = locals[cdt] && locals[cdt][cdn];
    if (!row) return;
    const product = row.product;
    // determine warehouse to use: prefer to_warehouse, then from_warehouse
    const warehouse = row.from_warehouse;
    if (!product || !warehouse) return;

    frappe.db.get_list('Stock Ledger Entry', {
        fields: ['ma_valuation'],
        filters: [ ['product', '=', product], ['warehouse', '=', warehouse] ],
        order_by: 'creation desc',
        limit_page_length: 1,
    }).then(res => {
        if (res && res.length && res[0].ma_valuation != null) {
            frappe.model.set_value(cdt, cdn, 'valuation', res[0].ma_valuation);
            // also refresh grid
            try { frm.refresh_field('item_list'); } catch (e) {}
        }
    }).catch(() => {});
}

// Child-table event handlers: react when product or warehouse fields change
frappe.ui.form.on('Items', {
    product(frm, cdt, cdn) {
        fetch_and_set_valuation(frm, cdt, cdn);
    },
    from_warehouse(frm, cdt, cdn) {
        fetch_and_set_valuation(frm, cdt, cdn);
    },
    to_warehouse(frm, cdt, cdn) {
        fetch_and_set_valuation(frm, cdt, cdn);
    }
});


