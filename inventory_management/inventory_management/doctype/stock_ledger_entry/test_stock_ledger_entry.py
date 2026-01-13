# Copyright (c) 2026, Krishna and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from math import isclose

# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]



class IntegrationTestStockLedgerEntry(IntegrationTestCase):
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
