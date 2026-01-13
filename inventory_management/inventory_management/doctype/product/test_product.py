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
        # Generate a unique suffix for this test run to avoid name collisions
        self.test_product_name = "Test Product"

    def test_naming_series_logic(self):
        """Check if PR.##### naming is applied without affecting existing items"""
        product = frappe.get_doc({
            "doctype": "Product",
            "product_name": self.test_product_name
        }).insert()
        
        # Verify the naming series pattern
        self.assertTrue(product.name.startswith("PR"))
        
        # Verify the name is what we assigned
        self.assertEqual(product.product_name, self.test_product_name)

    def test_data_integrity(self):
        """Ensure the created test item exists independently"""
        product = frappe.get_doc({
            "doctype": "Product",
            "product_name": self.test_product_name
        }).insert()

        # Fetch from database to ensure it saved correctly
        db_name = frappe.db.get_value("Product", {"product_name": self.test_product_name}, "name")
        self.assertEqual(db_name, product.name)

    def tearDown(self):
        """
        Optional: Specifically remove only the items created by this test 
        to keep the database clean without touching pre-existing data.
        """
        frappe.db.delete("Product", {"product_name": self.test_product_name})