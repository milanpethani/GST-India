from india_compliance.gst_india.utils import delete_old_fields


def execute():
    delete_old_fields(
        "customer_gstin",
        (
            "Quotation",
            "Sales Order",
            "Delivery Note",
            "Sales Invoice",
            "POS Invoice",
        ),
    )

    delete_old_fields("reason_for_issuing_document", "Purchase Invoice")
    delete_old_fields("pan_details", "Company")
    delete_old_fields("export_type", ("Customer", "Supplier"))
