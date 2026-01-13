# Copyright (c) 2026, Krishna and Contributors
# See license.txt

# import frappe
import frappe
from frappe.tests import IntegrationTestCase


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]



class IntegrationTestWarehouse(IntegrationTestCase):
	"""
	Integration tests for Warehouse.
	Use this class for testing interactions between multiple components.
	"""

	def test_create_warehouse(self):
		"""Create a Warehouse record, verify it exists, then delete it."""

		name = f"Test Warehouse {self._testMethodName}"

		# Create (basic)
		w = frappe.get_doc({"doctype": "Warehouse", "warehouse_name": name})
		w.insert()

		# Verify created: existence, name pattern and default flags
		self.assertTrue(frappe.db.exists("Warehouse", w.name))
		created = frappe.get_doc("Warehouse", w.name)
		self.assertEqual(created.warehouse_name, name)
		self.assertTrue(created.name.startswith("WA"))
		self.assertFalse(bool(created.is_group))

		# Cleanup
		created.delete()

	def test_mandatory_fields_and_parent(self):
		"""Edge cases: missing mandatory field and parent-child creation."""

		# Missing mandatory field should raise MandatoryError
		doc = frappe.get_doc({"doctype": "Warehouse"})
		self.assertRaises(frappe.MandatoryError, doc.insert)

		# Create a parent (group) warehouse and a child warehouse referencing it
		parent_name = f"Parent WH {self._testMethodName}"
		parent = frappe.get_doc({"doctype": "Warehouse", "warehouse_name": parent_name, "is_group": 1})
		parent.insert()

		child_name = f"Child WH {self._testMethodName}"
		child = frappe.get_doc(
			{"doctype": "Warehouse", "warehouse_name": child_name, "parent_warehouse": parent.name}
		)
		child.insert()

		# Verify linkage
		child_refetched = frappe.get_doc("Warehouse", child.name)
		self.assertEqual(child_refetched.parent_warehouse, parent.name)

		# Cleanup
		child_refetched.delete()
		parent.delete()
