frappe.ui.form.on('Purchase Order', {
    refresh: function(frm) {
        // Add validation when supplier field changes
        frm.fields_dict['supplier'].df.change = function() {
            if (frm.doc.supplier) {
                validate_supplier(frm);
            }
        };
    },
    
    onload: function(frm) {
        // Initial validation if supplier is already set
        if (frm.doc.supplier) {
            validate_supplier(frm);
        }
    }
});

function validate_supplier(frm) {
    if (!frm.doc.supplier) {
        return;
    }

    // Check onboarding state for the supplier (approved or management override)
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Supplier Onboarding',
            filters: {
                supplier: frm.doc.supplier
            },
            fields: ['name', 'onboarding_status', 'supplier_enable_override'],
            order_by: 'creation desc',
            limit: 20
        },
        callback: function(r) {
            let rows = r.message || [];
            let onboarding_approved = rows.some(function(row) {
                return row.onboarding_status === 'Approved';
            });
            let override_active = rows.some(function(row) {
                return !!row.supplier_enable_override && row.onboarding_status !== 'Approved';
            });
            let approved_or_overridden = onboarding_approved || override_active;

            // Also check if supplier is enabled
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Supplier',
                    name: frm.doc.supplier,
                    fields: ['name', 'status']
                },
                callback: function(supplier_r) {
                    let supplier_enabled = supplier_r.message && supplier_r.message.status !== 'Disabled';

                    if (approved_or_overridden && supplier_enabled) {
                        if (override_active) {
                            frappe.msgprint({
                                title: __('Management Override'),
                                message: __('This supplier is enabled by a management override and has not completed formal onboarding approval. Proceed with care.'),
                                indicator: 'orange'
                            });
                        }
                        return;
                    }

                    if (!frappe.user_roles.includes('Vendor Management')) {
                        let error_message = '';
                        if (!approved_or_overridden && !supplier_enabled) {
                            error_message = 'This supplier has not completed the onboarding process and is disabled. Purchase Order cannot be created.';
                        } else if (!approved_or_overridden) {
                            error_message = 'This supplier has not completed the onboarding process. Purchase Order cannot be created.';
                        } else {
                            error_message = 'This supplier is disabled. Purchase Order cannot be created.';
                        }

                        frappe.msgprint({
                            title: __('Supplier Not Approved'),
                            message: __(error_message),
                            indicator: 'red'
                        });
                        frm.set_value('supplier', '');
                    } else {
                        let warning_message = '';
                        if (override_active) {
                            warning_message = 'This supplier is enabled by management override and is not formally approved. You are creating an emergency Purchase Order.';
                        } else if (!approved_or_overridden && !supplier_enabled) {
                            warning_message = 'This supplier is not approved and is disabled. You are creating an emergency Purchase Order.';
                        } else if (!approved_or_overridden) {
                            warning_message = 'This supplier is not approved. You are creating an emergency Purchase Order.';
                        } else {
                            warning_message = 'This supplier is disabled. You are creating an emergency Purchase Order.';
                        }

                        frappe.msgprint({
                            title: __('Emergency PO'),
                            message: __(warning_message),
                            indicator: 'orange'
                        });
                    }
                }
            });
        }
    });
}