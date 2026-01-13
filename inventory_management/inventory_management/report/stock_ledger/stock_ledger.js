// Copyright (c) 2026, Krishna and contributors
// For license information, please see license.txt

frappe.query_reports["Stock Ledger"] = {
	filters: [
		{
		"fieldname": "product",
		"fieldtype": "Link",
		"label": "Product",
		"mandatory": 0,
		"options": "product",
		"wildcard_filter": 0
		},
		{
		"fieldname": "warehouse",
		"fieldtype": "Link",
		"label": "Warehouse",
		"mandatory": 0,
		"options": "warehouse",
		"wildcard_filter": 0
		},
		{
		"fieldname": "from_datetime",
		"fieldtype": "Datetime",
		"label": "From",
		"mandatory": 0,
		"wildcard_filter": 0
		},
		{
		"fieldname": "to_datetime",
		"fieldtype": "Datetime",
		"label": "To",
		"mandatory": 0,
		"wildcard_filter": 0
		}
	],
};
