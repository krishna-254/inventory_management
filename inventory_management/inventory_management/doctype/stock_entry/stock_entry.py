# Copyright (c) 2026, Krishna and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


def get_warehouse_product_qty(warehouse,product):
	query = frappe.qb.get_query(
		"Stock Ledger Entry",
		fields=[{"SUM":"quantity_change","as":"total_quantity"}],
		filters=[
			["product",'=',product],
			["warehouse","=",warehouse]
		]
	)
	return query.run(pluck=True)[0]

class StockEntry(Document):
	def before_submit(self):
		self.validate_transaction_warehouses()

		self.validate_from_warehouse()

	def validate_transaction_warehouses(self):

		tt = (self.transaction_type or "").strip()
		if tt == "Receipt":
			if not self.to_warehouse:
				frappe.throw("`to_warehouse` must be set for Receipt transactions")
			if self.from_warehouse:
				frappe.throw("`from_warehouse` must be empty for Receipt transactions")
			self._validate_warehouse_exists_and_is_not_group(self.to_warehouse)
		elif tt == "Consume":
			if not self.from_warehouse:
				frappe.throw("`from_warehouse` must be set for Consume transactions")
			if self.to_warehouse:
				frappe.throw("`to_warehouse` must be empty for Consume transactions")
			self._validate_warehouse_exists_and_is_not_group(self.from_warehouse)
		elif tt == "Transfer":
			if not self.from_warehouse or not self.to_warehouse:
				frappe.throw("Both `from_warehouse` and `to_warehouse` must be set for Transfer transactions")
			if self.from_warehouse == self.to_warehouse:
				frappe.throw("`from_warehouse` and `to_warehouse` must be different for Transfer transactions")
			self._validate_warehouse_exists_and_is_not_group(self.from_warehouse)
			self._validate_warehouse_exists_and_is_not_group(self.to_warehouse)
		else:
			# For other/unknown types, be permissive but validate any provided warehouses
			if self.from_warehouse:
				self._validate_warehouse_exists_and_is_not_group(self.from_warehouse)
			if self.to_warehouse:
				self._validate_warehouse_exists_and_is_not_group(self.to_warehouse)

	def _validate_warehouse_exists_and_is_not_group(self, warehouse_name):
		if not warehouse_name:
			return
		w = frappe.get_doc("Warehouse", warehouse_name)
		if getattr(w, "is_group", 0):
			frappe.throw(f"Warehouse {warehouse_name} is a group and cannot be used for Stock Entry")



	def validate_from_warehouse(self):
		if not self.from_warehouse:
			return

		item_list = self.get("item_list")
		for item in item_list:
			warehouse_qty = get_warehouse_product_qty(self.from_warehouse, item.product)
			if warehouse_qty < item.quantity:
				frappe.throw(f"{item.product} quantity in {self.from_warehouse} is {warehouse_qty}")
			
	
	def on_submit(self):

		item_list = self.get("item_list")
		for item in item_list:
			self.create_ledgers(item)
			

	def create_ledgers(self,item):

		if self.from_warehouse:
			from_ledger = frappe.new_doc("Stock Ledger Entry")
			from_ledger.time_stamp = frappe.utils.now()

			from_ledger.warehouse = self.from_warehouse
			from_ledger.product = item.product
			from_ledger.quantity_change = -item.quantity
			from_ledger.incomming_valuation = 0
			from_ledger.insert()
		
		if self.to_warehouse:
			to_ledger = frappe.new_doc("Stock Ledger Entry")
			to_ledger.time_stamp = frappe.utils.now()

			to_ledger.warehouse = self.to_warehouse
			to_ledger.product = item.product
			to_ledger.quantity_change = item.quantity
			to_ledger.incomming_valuation = item.valuation

			product_warehouse_qty = get_warehouse_product_qty(to_ledger.warehouse,to_ledger.product)

			try:
				latest_ledger = frappe.get_last_doc(
					"Stock Ledger Entry",
					filters=[
						["product",'=',to_ledger.product],
						["warehouse","=",to_ledger.warehouse]
					]
				)
				previous_ma = latest_ledger.ma_valuation

				moving_average = ((previous_ma * product_warehouse_qty)+(item.valuation * item.quantity)) / (product_warehouse_qty + item.quantity)

			except:
				moving_average = item.valuation

			to_ledger.ma_valuation = moving_average
			
			to_ledger.insert()



