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
		item_list = self.get("item_list") or []

		# Helper to obtain warehouse values from item row or fall back to doc-level
		def _item_from_wh(item):
			if isinstance(item, dict):
				return item.get("from_warehouse")
			return getattr(item, "from_warehouse", None)

		def _item_to_wh(item):
			if isinstance(item, dict):
				return item.get("to_warehouse")
			return getattr(item, "to_warehouse", None)

		if tt == "Receipt":
			# Each item must provide to_warehouse (preferred) or document-level to_warehouse
			for item in item_list:
				to_wh = _item_to_wh(item)
				from_wh = _item_from_wh(item)
				if from_wh:
					frappe.throw("`from_warehouse` must be empty for Receipt transactions (use item-level to_warehouse only)")
				if not to_wh and not self.to_warehouse:
					frappe.throw("`to_warehouse` must be set for Receipt transactions (at item row or document)")
				if to_wh:
					self._validate_warehouse_exists_and_is_not_group(to_wh)
			if not item_list and not self.to_warehouse:
				frappe.throw("`to_warehouse` must be set for Receipt transactions")

		elif tt == "Consume":
			for item in item_list:
				from_wh = _item_from_wh(item)
				to_wh = _item_to_wh(item)
				if to_wh:
					frappe.throw("`to_warehouse` must be empty for Consume transactions (use item-level from_warehouse only)")
				if not from_wh and not self.from_warehouse:
					frappe.throw("`from_warehouse` must be set for Consume transactions (at item row or document)")
				if from_wh:
					self._validate_warehouse_exists_and_is_not_group(from_wh)
			if not item_list and not self.from_warehouse:
				frappe.throw("`from_warehouse` must be set for Consume transactions")

		elif tt == "Transfer":
			for item in item_list:
				from_wh = _item_from_wh(item)
				to_wh = _item_to_wh(item)
				# allow fallback to document-level if item doesn't specify
				from_wh = from_wh or self.from_warehouse
				to_wh = to_wh or self.to_warehouse
				if not from_wh or not to_wh:
					frappe.throw("Both `from_warehouse` and `to_warehouse` must be set for Transfer transactions (at item row or document)")
				if from_wh == to_wh:
					frappe.throw("`from_warehouse` and `to_warehouse` must be different for Transfer transactions")
				self._validate_warehouse_exists_and_is_not_group(from_wh)
				self._validate_warehouse_exists_and_is_not_group(to_wh)

		else:
			# For other/unknown types, validate any provided warehouses on items or document
			for item in item_list:
				from_wh = _item_from_wh(item) or self.from_warehouse
				to_wh = _item_to_wh(item) or self.to_warehouse
				if from_wh:
					self._validate_warehouse_exists_and_is_not_group(from_wh)
				if to_wh:
					self._validate_warehouse_exists_and_is_not_group(to_wh)

	def _validate_warehouse_exists_and_is_not_group(self, warehouse_name):
		if not warehouse_name:
			return
		w = frappe.get_doc("Warehouse", warehouse_name)
		if getattr(w, "is_group", 0):
			frappe.throw(f"Warehouse {warehouse_name} is a group and cannot be used for Stock Entry")



	def validate_from_warehouse(self):
		# Validate availability for each item using item-level from_warehouse if provided,
		# otherwise fall back to document-level `from_warehouse`.
		item_list = self.get("item_list") or []
		for item in item_list:
			# support both dict-style and attribute-style access
			if isinstance(item, dict):
				item_from_wh = item.get("from_warehouse")
			else:
				item_from_wh = getattr(item, "from_warehouse", None)
			warehouse_to_check = item_from_wh or self.from_warehouse
			if not warehouse_to_check:
				continue
			warehouse_qty = get_warehouse_product_qty(warehouse_to_check, item.product)
			if warehouse_qty < item.quantity:
				frappe.throw(f"{item.product} quantity in {warehouse_to_check} is {warehouse_qty}")
			
	
	def on_submit(self):

		item_list = self.get("item_list")
		for item in item_list:
			self.create_ledgers(item)
			

	def create_ledgers(self,item):

		# Determine item-level warehouses with document-level fallback
		if isinstance(item, dict):
			item_from_wh = item.get("from_warehouse")
			item_to_wh = item.get("to_warehouse")
		else:
			item_from_wh = getattr(item, "from_warehouse", None)
			item_to_wh = getattr(item, "to_warehouse", None)
		from_wh = item_from_wh or self.from_warehouse
		to_wh = item_to_wh or self.to_warehouse

		if from_wh:
			from_ledger = frappe.new_doc("Stock Ledger Entry")
			from_ledger.time_stamp = frappe.utils.now()

			from_ledger.warehouse = from_wh
			from_ledger.product = item.product
			from_ledger.quantity_change = -item.quantity
			from_ledger.incomming_valuation = 0
			from_ledger.insert()

		if to_wh:
			to_ledger = frappe.new_doc("Stock Ledger Entry")
			to_ledger.time_stamp = frappe.utils.now()

			to_ledger.warehouse = to_wh
			to_ledger.product = item.product
			to_ledger.quantity_change = item.quantity
			# Determine incoming valuation from the latest MA if available, otherwise fallback to item valuation
			product_warehouse_qty = get_warehouse_product_qty(to_ledger.warehouse, to_ledger.product)

			try:
				latest_ledger = frappe.get_last_doc(
					"Stock Ledger Entry",
					filters=[
						["product", "=", to_ledger.product],
						["warehouse", "=", to_ledger.warehouse],
					]
				)
				previous_ma = latest_ledger.ma_valuation
				# incoming valuation should come from the item (frontend sets it)
				incoming_val = item.valuation
				moving_average = ((previous_ma * product_warehouse_qty) + (incoming_val * item.quantity)) / (
					product_warehouse_qty + item.quantity
				)

			except Exception:
				# no previous ledger -> use item valuation
				incoming_val = item.valuation
				moving_average = item.valuation

			to_ledger.incomming_valuation = incoming_val
			to_ledger.ma_valuation = moving_average
			to_ledger.insert()



