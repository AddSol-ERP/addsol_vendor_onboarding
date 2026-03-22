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
    // Check if supplier is approved and enabled
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Supplier Onboarding',
            filters: {
                supplier: frm.doc.supplier,
                onboarding_status: 'Approved'
            },
            fields: ['name', 'onboarding_status']
        },
        callback: function(r) {
            let onboarding_approved = r.message && r.message.length > 0;
            
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
                    
                    if (!onboarding_approved || !supplier_enabled) {
                        // Check if user has Vendor Management role
                        if (!frappe.user_roles.includes('Vendor Management')) {
                            let error_message = '';
                            if (!onboarding_approved && !supplier_enabled) {
                                error_message = 'This supplier has not completed the onboarding process and is disabled. Purchase Order cannot be created.';
                            } else if (!onboarding_approved) {
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
                            if (!onboarding_approved && !supplier_enabled) {
                                warning_message = 'This supplier is not approved and is disabled. You are creating an emergency Purchase Order.';
                            } else if (!onboarding_approved) {
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
                }
            });
        }
    });
}