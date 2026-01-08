# Copyright (c) 2026, Krishna and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class StockEntry(Document):
	def after_save(self):
		from_ledger = frappe.new_doc("Stock Ledger Entry")
		to_ledger = frappe.new_doc("Stock Ledger Entry")

		#From Warehouse ledger
		from_ledger.warehouse = self.from_warehouse
		from_ledger.product = self.product

	# def validate_warehouse_products(self):
	# 	item_list = self.get("item_list")
	# 	string = ""
	# 	for item in item_list:
	# 		product = frappe.get_doc("Product", item.product)
	# 		string += f"{product},"
	# 	frappe.throw(string)

	# def validate_qty(self, product):
	# 	warehouse_product_qty =frappe.get_doc("Warehouse", self.from_warehouse)
	# 	if warehouse_product_qty < product