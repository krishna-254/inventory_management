# Copyright (c) 2026, Krishna and contributors
# For license information, please see license.txt

# import frappe
from frappe import _
import frappe
from frappe.query_builder.functions import Sum

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
			"label": _("Warehouse"),
			"fieldname": "warehouse",
			"fieldtype": "Data",
		},
		{
			"label": _("Product"),
			"fieldname": "product",
			"fieldtype": "Data",
		},
		{
			"label": _("Total Stock"),
			"fieldname": "total_stock",
			"fieldtype": "Int",
		},
		{
			"label": _("Balance"),
			"fieldname": "balance",
			"fieldtype": "Currency",
		},
		{
			"label": _("Moving Average Valuation"),
			"fieldname": "ma_valuation",
			"fieldtype": "Currency",
		},
	]



def get_data(filters: dict) -> list[list]:
	"""Return data for the report.

	The report data is a list of rows, with each row being a list of cell values.
	"""

	ledger = frappe.qb.DocType("Stock Ledger Entry")
	query = frappe.qb.from_(ledger)

	query = query.select(
		ledger.name,
		ledger.warehouse,
		ledger.product,
		ledger.time_stamp
	)

	if filters.get("time_stamp"):
		query = query.where(
			ledger.time_stamp <= filters.get("time_stamp")
		)

	if filters.get("warehouse"):
		child_warehouses = frappe.get_all("Warehouse", {"name":("descendants of", filters.get("warehouse"))}, pluck="name")
		child_warehouses.append(filters.get("warehouse"))
		query = query.where(
			ledger.warehouse.isin(child_warehouses)
		)
	
	if filters.get("product"):
		query = query.where(
			ledger.product == filters.get("product")
		)

	
	query = query.select(
		Sum(ledger.incomming_valuation).as_("total_value"),
		Sum(ledger.quantity_change).as_("total_stock"),
		(Sum(ledger.incomming_valuation* ledger.quantity_change)).as_("balance"),
		((Sum(ledger.incomming_valuation* ledger.quantity_change))/Sum(ledger.quantity_change)).as_("ma_valuation"),
	).groupby(
		ledger.warehouse,
		ledger.product
	)



	# frappe.throw(f"{query.run(debug=True)}")

	return query.run(as_dict=True)
