# Copyright (c) 2026, Krishna and contributors
# For license information, please see license.txt

# import frappe
from frappe import _
import frappe

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
		"fieldname": "time_stamp",
		"fieldtype": "Datetime",
		"label": "Time Stamp",
		"width": 0
		},
		{
		"fieldname": "product",
		"fieldtype": "Link",
		"label": "Product",
		"options": "product",
		"width": 0
		},
		{
		"fieldname": "warehouse",
		"fieldtype": "Link",
		"label": "Warehouse",
		"options": "warehouse",
		"width": 0
		},
		{
		"fieldname": "quantity_change",
		"fieldtype": "Int",
		"label": "Quantity Change",
		"width": 0
		},
		{
		"fieldname": "incomming_valuation",
		"fieldtype": "Currency",
		"label": "Incomming Valuation",
		"width": 0
		}
	]


def get_data(filters) -> list[list]:
	"""Return data for the report.

	The report data is a list of rows, with each row being a list of cell values.
	"""

	ledger = frappe.qb.DocType("Stock Ledger Entry")
	query = frappe.qb.from_(ledger)


	query = query.select(
		ledger.time_stamp,
		ledger.product,
		ledger.warehouse,
		ledger.quantity_change,
		ledger.incomming_valuation
		# ledger.name,
	)

	if filters.get("product"):
		query = query.where(
			ledger.product == filters.get("product")
		)
	
	if filters.get("warehouse"):
		query = query.where(
			ledger.warehouse == filters.get("warehouse")
		)

	if filters.get("from_datetime"):
		query = query.where(
			ledger.time_stamp >= filters.get("from_datetime")
		)

	if filters.get("to_datetime"):
		query = query.where(
			ledger.time_stamp <= filters.get("to_datetime")
		)

	return query.run(as_dict=True)



