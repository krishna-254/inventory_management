# Copyright (c) 2026, Krishna and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters: dict | None = None):
	"""Return columns and data for the report.

	This is the main entry point for the report. It accepts the filters as a
	dictionary and should return columns and data. It is called by the framework
	every time the report is refreshed or a filter is updated.
	"""
	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns() -> list[dict]:
	"""Return columns for the report.

	One field definition per column, just like a DocType field definition.
	"""
	
	return [
		{
		"fieldname": "warehouse",
		"fieldtype": "Data",
		"label": "Warehouse",
		"width": 0
		},
		{
		"fieldname": "product",
		"fieldtype": "Data",
		"label": "Product",
		"width": 0
		},
		{
		"fieldname": "time_stamp",
		"fieldtype": "Datetime",
		"label": "Time Stamp",
		"width": 0
		},
		{
		"fieldname": "ma_valuation",
		"fieldtype": "Currency",
		"label": "Moving Average Valuation",
		"width": 0
		}
	]


def get_data(filters: dict | None = None):
	"""Return data for the report.

	The report data is a list of rows, with each row being a list of cell values.
	"""
	
	stock_ledger = frappe.qb.DocType("Stock Ledger Entry")
	query = frappe.qb.from_(stock_ledger)
	query = query.select(
		stock_ledger.warehouse,
		stock_ledger.product,
		stock_ledger.time_stamp,
		stock_ledger.ma_valuation
	).where(
		(stock_ledger.ma_valuation > 0)
	)


	return query.run(as_dict=True)