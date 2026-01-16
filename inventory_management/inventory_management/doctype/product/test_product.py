# Copyright (c) 2026, Krishna and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]



class IntegrationTestProduct(IntegrationTestCase):
    def setUp(self):
        # Unique name per test method to avoid collisions
        self.test_product_name = f"Test Product {self._testMethodName}"

    def test_naming_series_logic(self):
        """Check if PR##### naming is applied and product is saved."""
        product = frappe.get_doc({
            "doctype": "Product",
            "product_name": self.test_product_name,
        }).insert()

        # Verify the naming series pattern
        self.assertTrue(product.name.startswith("PR"))
        # Verify the product_name was set
        self.assertEqual(product.product_name, self.test_product_name)

    def test_data_integrity(self):
        """Ensure the created test product exists in DB."""
        product = frappe.get_doc({"doctype": "Product", "product_name": self.test_product_name}).insert()
        db_name = frappe.db.get_value("Product", {"product_name": self.test_product_name}, "name")
        self.assertEqual(db_name, product.name)

    def test_create_update_delete_product(self):
        """Create a product, update its name, and delete it."""
        # Create
        p = frappe.get_doc({"doctype": "Product", "product_name": self.test_product_name})
        p.insert()
        self.assertTrue(frappe.db.exists("Product", p.name))

        # Update
        p.product_name = self.test_product_name + " Updated"
        p.save()
        updated = frappe.get_doc("Product", p.name)
        self.assertEqual(updated.product_name, self.test_product_name + " Updated")

        # Delete
        frappe.delete_doc("Product", p.name)
        self.assertFalse(frappe.db.exists("Product", p.name))

    def test_mandatory_field_validation(self):
        """Inserting Product without required `product_name` should raise MandatoryError."""
        doc = frappe.get_doc({"doctype": "Product"})
        self.assertRaises(frappe.MandatoryError, doc.insert)

    def tearDown(self):
        # Clean up any products created during tests
        try:
            frappe.db.delete("Product", {"product_name": self.test_product_name})
        except Exception:
            pass
        try:
            frappe.db.delete("Product", {"product_name": self.test_product_name + " Updated"})
        except Exception:
            pass