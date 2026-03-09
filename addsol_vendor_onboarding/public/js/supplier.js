frappe.ui.form.on('Supplier', {
    refresh: function(frm) {
        if (!frm.doc.__islocal) {
            // Add button to initiate onboarding
            frm.add_custom_button(__('Start Onboarding'), function() {
                start_onboarding(frm);
            }, __('Actions'));
            
            // Show onboarding status
            show_onboarding_status(frm);
        }
    }
});

function start_onboarding(frm) {
    // Check if onboarding already exists
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Supplier Onboarding',
            filters: {
                supplier: frm.doc.name
            },
            fields: ['name', 'onboarding_status']
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                let existing = r.message[0];
                frappe.msgprint({
                    title: __('Onboarding Exists'),
                    message: __('Onboarding process already initiated for this supplier. Status: {0}', [existing.onboarding_status]),
                    indicator: 'blue'
                });
                frappe.set_route('Form', 'Supplier Onboarding', existing.name);
            } else {
                // Create new onboarding
                frappe.call({
                    method: 'frappe.client.insert',
                    args: {
                        doc: {
                            doctype: 'Supplier Onboarding',
                            supplier: frm.doc.name,
                            supplier_name: frm.doc.supplier_name,
                            email: frm.doc.email_id,
                            phone_number: frm.doc.mobile_no,
                            ...(frm.doc.gstin && { gstn: frm.doc.gstin }),
                            ...(frm.doc.pan && { pan: frm.doc.pan }),
                            ...(frm.doc.cin_llpin && { cin: frm.doc.cin_llpin }),
                            ...(frm.doc.bank_account_no && { bank_account_no: frm.doc.bank_account_no }),
                            ...(frm.doc.bank_ifsc_code && { bank_ifsc: frm.doc.bank_ifsc_code }),
                            ...(frm.doc.udyam_registration_number && { udyog_aadhaar: frm.doc.udyam_registration_number })
                        }
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.show_alert({
                                message: __('Onboarding Process Started'),
                                indicator: 'green'
                            });
                            frappe.set_route('Form', 'Supplier Onboarding', r.message.name);
                        }
                    }
                });
            }
        }
    });
}

function show_onboarding_status(frm) {
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Supplier Onboarding',
            filters: {
                supplier: frm.doc.name
            },
            fields: ['name', 'onboarding_status', 'validation_status'],
            order_by: 'modified desc',
            limit: 1
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                let status = r.message[0];
                let color = 'blue';
                
                if (status.onboarding_status === 'Approved') {
                    color = 'green';
                } else if (status.onboarding_status === 'Rejected') {
                    color = 'red';
                } else if (status.onboarding_status === 'Validation Failed') {
                    color = 'orange';
                }
                
                frm.dashboard.add_indicator(
                    __('Onboarding Status: {0}', [status.onboarding_status]),
                    color
                );
            }
        }
    });
}