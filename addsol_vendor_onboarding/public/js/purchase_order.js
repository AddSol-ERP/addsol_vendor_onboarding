frappe.ui.form.on('Purchase Order', {
    supplier: function(frm) {
        if (frm.doc.supplier) {
            // Check if supplier is approved
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
                    if (!r.message || r.message.length === 0) {
                        // Check if user has Vendor Management role
                        if (!frappe.user_roles.includes('Vendor Management')) {
                            frappe.msgprint({
                                title: __('Supplier Not Approved'),
                                message: __('This supplier has not completed the onboarding process. Purchase Order cannot be created.'),
                                indicator: 'red'
                            });
                            frm.set_value('supplier', '');
                        } else {
                            frappe.msgprint({
                                title: __('Emergency PO'),
                                message: __('This supplier is not approved. You are creating an emergency Purchase Order.'),
                                indicator: 'orange'
                            });
                        }
                    }
                }
            });
        }
    }
});