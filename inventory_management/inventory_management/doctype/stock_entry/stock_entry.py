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
		self.validate_from_warehouse()



	def validate_from_warehouse(self):
		if not self.from_warehouse: return

		item_list = self.get("item_list")
		for item in item_list:
			warehouse_qty = get_warehouse_product_qty(self.from_warehouse,item.product)
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
			from_ledger.incomming_valuation = item.valuation
			from_ledger.insert()
		
		if self.to_warehouse:
			to_ledger = frappe.new_doc("Stock Ledger Entry")
			to_ledger.time_stamp = frappe.utils.now()

			to_ledger.warehouse = self.to_warehouse
			to_ledger.product = item.product
			to_ledger.quantity_change = item.quantity
			to_ledger.incomming_valuation = item.valuation

			# query = frappe.qb.get_query(
			# 	"Stock Ledger Entry",
			# 	fields=[{"SUM":"quantity_change","as":"total_quantity"}],
			# 	filters=[
			# 		["product",'=',to_ledger.product],
			# 		["warehouse","=",to_ledger.warehouse]
			# 	]
			# )
			product_warehouse_qty = get_warehouse_product_qty(to_ledger.warehouse,to_ledger.product)


			# query = frappe.qb.get_query(
			# 	"Stock Ledger Entry",
			# 	fields=["ma_valuation"],
			# 	filters=[
			# 		["product",'=',to_ledger.product],
			# 		["warehouse","=",to_ledger.warehouse]
			# 	]
			# )
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



