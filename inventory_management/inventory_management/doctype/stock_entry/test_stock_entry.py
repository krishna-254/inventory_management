# Copyright (c) 2026, Krishna and Contributors
# See license.txt

# import frappe
import frappe
from frappe.tests import IntegrationTestCase
from math import isclose

# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]



class IntegrationTestStockEntry(IntegrationTestCase):
	"""
	Integration tests for StockEntry.
	Use this class for testing interactions between multiple components.
	"""

	def _create_product(self, name=None):
		name = name or f"PR-{self._testMethodName}"
		p = frappe.get_doc({"doctype": "Product", "product_name": name})
		p.insert()
		return p

	def _create_warehouse(self, name=None, is_group=0):
		name = name or f"WH-{self._testMethodName}"
		w = frappe.get_doc({"doctype": "Warehouse", "warehouse_name": name, "is_group": is_group})
		w.insert()
		return w

	def _cleanup_docs(self, doctype, names):
		for n in names:
			try:
				frappe.delete_doc(doctype, n)
			except Exception:
				pass

	# Ledger-specific tests were moved to test_stock_ledger.py

	def test_transfer_and_insufficient_qty(self):
		"""Test transfer creates paired ledgers and raising on insufficient stock."""

		product = self._create_product("TransferProduct")
		wh_from = self._create_warehouse("FromWH", is_group=0)
		wh_to = self._create_warehouse("ToWH", is_group=0)

		# Add initial 5 units to from warehouse
		se_init = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"transaction_type": "Receipt",
				"to_warehouse": wh_from.name,
				"item_list": [{"product": product.name, "quantity": 5, "valuation": 50}],
			}
		)
		se_init.insert()
		se_init.submit()

		# Transfer 3 units from FromWH to ToWH
		se_transfer = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"transaction_type": "Transfer",
				"from_warehouse": wh_from.name,
				"to_warehouse": wh_to.name,
				"item_list": [{"product": product.name, "quantity": 3, "valuation": 70}],
			}
		)
		se_transfer.insert()
		se_transfer.submit()

		# Verify quantities updated in warehouses
		# compute warehouse quantities via the same query used in production helper
		query = frappe.qb.get_query(
			"Stock Ledger Entry",
			fields=[{"SUM": "quantity_change", "as": "total_quantity"}],
			filters=[["product", "=", product.name], ["warehouse", "=", wh_from.name]],
		)
		qty_from = query.run(pluck=True)[0]

		query = frappe.qb.get_query(
			"Stock Ledger Entry",
			fields=[{"SUM": "quantity_change", "as": "total_quantity"}],
			filters=[["product", "=", product.name], ["warehouse", "=", wh_to.name]],
		)
		qty_to = query.run(pluck=True)[0]
		self.assertEqual(qty_from, 2)
		self.assertEqual(qty_to, 3)

		# Now attempt to transfer more than available (available in from_wh = 2)
		se_fail = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"transaction_type": "Transfer",
				"from_warehouse": wh_from.name,
				"to_warehouse": wh_to.name,
				"item_list": [{"product": product.name, "quantity": 10, "valuation": 80}],
			}
		)
		se_fail.insert()
		with self.assertRaises(frappe.ValidationError):
			se_fail.submit()

		# Cleanup
		ledger_names = [d.name for d in frappe.get_all("Stock Ledger Entry", filters={"product": product.name})]
		self._cleanup_docs("Stock Ledger Entry", ledger_names)
		for doc in (se_transfer, se_init):
			try:
				doc.cancel()
			except Exception:
				pass
			try:
				doc.delete()
			except Exception:
				pass
		self._cleanup_docs("Product", [product.name])
		self._cleanup_docs("Warehouse", [wh_from.name, wh_to.name])

	def test_ledgers_and_moving_average(self):
		"""Ensure Stock Ledger Entry records are created and MA valuation updates correctly."""

		product = self._create_product()
		warehouse = self._create_warehouse()

		# Create initial receipt: 10 units @ 100
		se1 = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"transaction_type": "Receipt",
				"to_warehouse": warehouse.name,
				"item_list": [{"product": product.name, "quantity": 10, "valuation": 100}],
			}
		)
		se1.insert()
		se1.submit()

		# Verify ledger created
		ledgers = frappe.get_all(
			"Stock Ledger Entry",
			filters={"product": product.name, "warehouse": warehouse.name},
			fields=["quantity_change", "incomming_valuation", "ma_valuation"],
			order_by="creation asc",
		)
		self.assertEqual(len(ledgers), 1)
		self.assertEqual(ledgers[0]["quantity_change"], 10)
		self.assertEqual(ledgers[0]["incomming_valuation"], 100)
		self.assertEqual(ledgers[0]["ma_valuation"], 100)

		# Add more stock: 5 units @ 120 -> new MA
		se2 = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"transaction_type": "Receipt",
				"to_warehouse": warehouse.name,
				"item_list": [{"product": product.name, "quantity": 5, "valuation": 120}],
			}
		)
		se2.insert()
		se2.submit()

		# Verify updated qty and MA
		query = frappe.qb.get_query(
			"Stock Ledger Entry",
			fields=[{"SUM": "quantity_change", "as": "total_quantity"}],
			filters=[["product", "=", product.name], ["warehouse", "=", warehouse.name]],
		)
		total_qty = query.run(pluck=True)[0]
		self.assertEqual(total_qty, 15)

		last_ledger = frappe.get_last_doc(
			"Stock Ledger Entry",
			filters=[["product", "=", product.name], ["warehouse", "=", warehouse.name]],
		)

		# expected MA: ((100*10)+(120*5))/15
		expected_ma = ((100 * 10) + (120 * 5)) / 15
		self.assertTrue(isclose(float(last_ledger.ma_valuation), expected_ma, rel_tol=1e-6))

		# Cleanup
		ledger_names = [d.name for d in frappe.get_all("Stock Ledger Entry", filters={"product": product.name})]
		self._cleanup_docs("Stock Ledger Entry", ledger_names)
		for doc in (se2, se1):
			try:
				doc.cancel()
			except Exception:
				pass
			try:
				doc.delete()
			except Exception:
				pass
		self._cleanup_docs("Product", [product.name])
		self._cleanup_docs("Warehouse", [warehouse.name])

	def test_receipt_validation_and_ledger(self):
		"""Receipt must have only `to_warehouse` and creates an incoming ledger."""

		product = self._create_product()
		warehouse = self._create_warehouse()

		# Receipt with both warehouses should raise
		se_bad = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"transaction_type": "Receipt",
				"from_warehouse": warehouse.name,
				"to_warehouse": warehouse.name,
				"item_list": [{"product": product.name, "quantity": 1, "valuation": 10}],
			}
		)
		se_bad.insert()
		with self.assertRaises(frappe.ValidationError):
			se_bad.submit()

		# Valid receipt
		se = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"transaction_type": "Receipt",
				"to_warehouse": warehouse.name,
				"item_list": [{"product": product.name, "quantity": 4, "valuation": 40}],
			}
		)
		se.insert()
		se.submit()

		# Verify incoming ledger created
		ledgers = frappe.get_all(
			"Stock Ledger Entry",
			filters={"product": product.name, "warehouse": warehouse.name},
			fields=["quantity_change", "incomming_valuation"],
			order_by="creation asc",
		)
		self.assertTrue(any(l["quantity_change"] == 4 for l in ledgers))
		self.assertTrue(any(l["incomming_valuation"] == 40 for l in ledgers))

		# Cleanup
		ledger_names = [d.name for d in frappe.get_all("Stock Ledger Entry", filters={"product": product.name})]
		self._cleanup_docs("Stock Ledger Entry", ledger_names)
		try:
			se.cancel()
		except Exception:
			pass
		try:
			se.delete()
		except Exception:
			pass
		self._cleanup_docs("Product", [product.name])
		self._cleanup_docs("Warehouse", [warehouse.name])

	def test_consume_validation_and_ledger(self):
		"""Consume must have only `from_warehouse` and creates an outgoing ledger."""

		product = self._create_product()
		warehouse = self._create_warehouse()

		# Seed with a receipt
		se_rec = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"transaction_type": "Receipt",
				"to_warehouse": warehouse.name,
				"item_list": [{"product": product.name, "quantity": 5, "valuation": 50}],
			}
		)
		se_rec.insert()
		se_rec.submit()

		# Consume without from_warehouse should raise
		se_bad = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"transaction_type": "Consume",
				"item_list": [{"product": product.name, "quantity": 2, "valuation": 0}],
			}
		)
		se_bad.insert()
		with self.assertRaises(frappe.ValidationError):
			se_bad.submit()

		# Valid consume
		se = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"transaction_type": "Consume",
				"from_warehouse": warehouse.name,
				"item_list": [{"product": product.name, "quantity": 3, "valuation": 0}],
			}
		)
		se.insert()
		se.submit()

		# Verify outgoing ledger created (negative quantity)
		last_ledger = frappe.get_last_doc(
			"Stock Ledger Entry",
			filters=[["product", "=", product.name], ["warehouse", "=", warehouse.name]],
		)
		self.assertEqual(last_ledger.quantity_change, -3)
		self.assertEqual(last_ledger.incomming_valuation, 0)

		# Cleanup
		ledger_names = [d.name for d in frappe.get_all("Stock Ledger Entry", filters={"product": product.name})]
		self._cleanup_docs("Stock Ledger Entry", ledger_names)
		for doc in (se, se_rec):
			try:
				doc.cancel()
			except Exception:
				pass
			try:
				doc.delete()
			except Exception:
				pass
		self._cleanup_docs("Product", [product.name])
		self._cleanup_docs("Warehouse", [warehouse.name])
