frappe.ui.form.on('Supplier Onboarding', {
    refresh: function(frm) {
        // Add custom buttons based on status
        if ((frm.doc.onboarding_status === 'Validation Successful' ||
             frm.doc.onboarding_status === 'Review Required') &&
            !frm.doc.__islocal && 
            frappe.user_roles.includes('Purchase Manager')) {
            
            frm.add_custom_button(__('Approve'), function() {
                approve_supplier(frm);
            }).addClass('btn-primary');
            
            frm.add_custom_button(__('Reject'), function() {
                reject_supplier(frm);
            }).addClass('btn-danger');
        }
        
        if (frm.doc.onboarding_status === 'Approved' && 
            !frm.doc.__islocal &&
            frappe.user_roles.includes('Purchase Manager')) {
            
            frm.add_custom_button(__('Re-initiate Verification'), function() {
                reinitiate_verification(frm);
            });
        }
        
        // Add button to trigger validation manually
        if (frm.doc.onboarding_status === 'Data Submitted' && 
            !frm.doc.__islocal &&
            frappe.user_roles.includes('Purchase Manager')) {
            
            frm.add_custom_button(__('Trigger Validation'), function() {
                trigger_validation(frm);
            });
        }

        // Add button to reconcile validation state from logs for this onboarding
        if (!frm.doc.__islocal &&
            (frappe.user_roles.includes('Purchase Manager') ||
             frappe.user_roles.includes('System Manager') ||
             frappe.user_roles.includes('Vendor Management'))) {

            frm.add_custom_button(__('Reconcile Validation Status'), function() {
                reconcile_validation_status(frm);
            }).addClass('btn-secondary');
        }
        
        // Add button to send a new private onboarding link manually
        if (frm.doc.email && !frm.doc.__islocal &&
            ['Pending Submission', 'Validation Failed', 'Rejected'].includes(frm.doc.onboarding_status) &&
            (frappe.user_roles.includes('Purchase Manager') || frappe.user_roles.includes('System Manager'))) {
            
            frm.add_custom_button(__('Send Private Link'), function() {
                send_credentials_manually(frm);
            }).addClass('btn-secondary');
        }
        
        // Show attached documents
        if (!frm.doc.__islocal) {
            show_attached_documents(frm);
            render_name_verification(frm);
        }
        
        // Set field properties based on status
        set_field_properties(frm);
    },
    
    onboarding_status: function(frm) {
        set_field_properties(frm);
    },
    
    supplier: function(frm) {
        if (frm.doc.supplier) {
            frappe.db.get_value('Supplier', frm.doc.supplier, 
                ['supplier_name', 'email_id'], function(r) {
                if (r) {
                    frm.set_value('supplier_name', r.supplier_name);
                    if (r.email_id) {
                        frm.set_value('email', r.email_id);
                    }
                }
            });
        }
    }
});

function approve_supplier(frm) {
    frappe.confirm(
        __('Are you sure you want to approve this supplier?'),
        function() {
            frappe.call({
                method: 'addsol_vendor_onboarding.addsol_vendor_onboarding.doctype.supplier_onboarding.supplier_onboarding.approve_supplier_onboarding',
                args: {
                    supplier_onboarding: frm.doc.name
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __('Supplier Approved Successfully'),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    }
                }
            });
        }
    );
}

function reject_supplier(frm) {
    frappe.prompt([
        {
            fieldname: 'reason',
            fieldtype: 'Text',
            label: 'Rejection Reason',
            reqd: 1
        }
    ],
    function(values) {
        frappe.call({
            method: 'addsol_vendor_onboarding.addsol_vendor_onboarding.doctype.supplier_onboarding.supplier_onboarding.reject_supplier_onboarding',
            args: {
                supplier_onboarding: frm.doc.name,
                reason: values.reason
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: __('Supplier Rejected'),
                        indicator: 'red'
                    });
                    frm.reload_doc();
                }
            }
        });
    },
    __('Reject Supplier'),
    __('Submit')
    );
}

function reinitiate_verification(frm) {
    frappe.prompt([
        {
            fieldname: 'reason',
            fieldtype: 'Text',
            label: 'Reason for Re-verification',
            reqd: 1
        }
    ],
    function(values) {
        frappe.call({
            method: 'addsol_vendor_onboarding.addsol_vendor_onboarding.doctype.supplier_onboarding.supplier_onboarding.reinitiate_verification',
            args: {
                supplier_onboarding: frm.doc.name,
                reason: values.reason
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: __('Re-verification Initiated'),
                        indicator: 'blue'
                    });
                    frm.reload_doc();
                }
            }
        });
    },
    __('Re-initiate Verification'),
    __('Submit')
    );
}

function trigger_validation(frm) {
    frappe.confirm(
        __('This will trigger the Automatic validation process. Continue?'),
        function() {
            frappe.call({
                method: 'addsol_vendor_onboarding.addsol_vendor_onboarding.doctype.supplier_onboarding.supplier_onboarding.trigger_supplier_onboarding_validation',
                args: {
                    supplier_onboarding: frm.doc.name
                },
                freeze: true,
                freeze_message: __('Triggering validation...'),
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __('Validation process started'),
                            indicator: 'blue'
                        });
                        frm.reload_doc();
                    }
                }
            });
        }
    );
}

function show_attached_documents(frm) {
    const formatFileSize = (size) => {
        const bytes = Number(size);
        if (!Number.isFinite(bytes) || bytes <= 0) {
            return __('Size unavailable');
        }
        if (bytes < 1024) {
            return `${bytes} B`;
        }
        if (bytes < 1024 * 1024) {
            return `${(bytes / 1024).toFixed(1)} KB`;
        }
        return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    };

    const escapeHtml = (value) => frappe.utils.escape_html(String(value || ''));

    frappe.call({
        method: 'get_attached_documents',
        doc: frm.doc,
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                let html = '<div class="attached-documents"><h4>Attached Documents:</h4><ul>';
                r.message.forEach(function(doc) {
                    const label = escapeHtml(doc.field_label || __('General Attachment'));
                    const fileName = escapeHtml(doc.file_name || __('Unnamed file'));
                    const fileUrl = escapeHtml(doc.file_url || '#');
                    const fileSize = formatFileSize(doc.file_size);
                    html += `<li><strong>${label}:</strong> <a href="${fileUrl}" target="_blank">${fileName}</a> (${fileSize})</li>`;
                });
                html += '</ul></div>';
                frm.get_field('documents_html').html(html);
            } else {
                frm.get_field('documents_html').html('<p>No documents attached</p>');
            }
        }
    });
}

function render_name_verification(frm) {
    const field = frm.get_field('name_verification_html');
    if (!field) {
        return;
    }

    const escapeHtml = (value) => frappe.utils.escape_html(String(value || ''));
    const checks = [
        { label: __('GSTN'), value_field: 'gstn', name_field: 'gstn_registered_name', match_field: 'gstn_name_match', flag_field: 'gstn_validated' },
        { label: __('PAN'), value_field: 'pan', name_field: 'pan_registered_name', match_field: 'pan_name_match', flag_field: 'pan_validated' },
        { label: __('CIN / LLPIN'), value_field: 'cin', name_field: 'cin_company_name', match_field: 'cin_name_match', flag_field: 'cin_validated' },
        { label: __('Bank Account'), value_field: 'bank_account_no', name_field: 'bank_account_name', match_field: 'bank_name_match', flag_field: 'bank_validated' },
        { label: __('Udyam Registration'), value_field: 'udyog_aadhaar', name_field: 'udyam_entity_name', match_field: 'udyam_name_match', flag_field: 'udyam_validated' }
    ];

    const supplierName = String(frm.doc.supplier_name || '').trim();
    let any_data = false;
    let rows = '';

    checks.forEach(function(check) {
        const entered = String(frm.doc[check.value_field] || '').trim();
        const registered = String(frm.doc[check.name_field] || '').trim();
        const verdict = frm.doc[check.match_field] || '';
        const validated = !!frm.doc[check.flag_field];

        const label_cell = escapeHtml(check.label) +
            (entered ? '<br><small class="text-muted">' + escapeHtml(entered) + '</small>' : '');

        if (!entered) {
            rows += '<tr>' +
                '<td>' + label_cell + '</td>' +
                '<td>' + escapeHtml(supplierName) + '</td>' +
                '<td>&ndash;</td>' +
                '<td><span class="indicator-pill gray">' + __('Not Provided') + '</span></td>' +
                '</tr>';
            return;
        }

        any_data = true;

        let badge;
        if (verdict === 'Matched') {
            badge = '<span class="indicator-pill green">' + __('Name Matched') + '</span>';
        } else if (verdict === 'Mismatch') {
            badge = '<span class="indicator-pill red">' + __('Name Mismatch') + '</span>';
        } else if (validated) {
            badge = '<span class="indicator-pill green">' + __('Validated') + '</span>';
        } else {
            badge = '<span class="indicator-pill gray">' + __('Not Verified') + '</span>';
        }

        rows += '<tr>' +
            '<td>' + label_cell + '</td>' +
            '<td>' + escapeHtml(supplierName) + '</td>' +
            '<td>' + (registered ? escapeHtml(registered) : '&ndash;') + '</td>' +
            '<td>' + badge + '</td>' +
            '</tr>';
    });

    if (!any_data) {
        field.html('');
        return;
    }

    let hint = '';
    if (frm.doc.onboarding_status === 'Review Required') {
        hint = '<p class="text-warning"><strong>' + __('Review Required:') + '</strong> ' +
            __('all identifiers are valid with the authorities, but at least one registered name differs from the supplier name on this record. Compare below, then Approve or Reject.') +
            '</p>';
    }

    field.html(
        '<div class="name-verification-comparison">' +
        '<p class="text-muted">' +
        __('Names registered against each identifier (as returned by the verification provider) compared with the supplier name on this record.') +
        '</p>' +
        hint +
        '<table class="table table-bordered table-sm">' +
        '<thead><tr>' +
        '<th>' + __('Check') + '</th>' +
        '<th>' + __('Supplier Name (Entered)') + '</th>' +
        '<th>' + __('Registered Name (Provider)') + '</th>' +
        '<th>' + __('Name Match') + '</th>' +
        '</tr></thead>' +
        '<tbody>' + rows + '</tbody>' +
        '</table>' +
        '</div>'
    );
}

function set_field_properties(frm) {
    // Lock fields after approval and while awaiting review decisions
    if (frm.doc.onboarding_status === 'Approved' || frm.doc.onboarding_status === 'Review Required') {
        frm.set_df_property('gstn', 'read_only', 1);
        frm.set_df_property('pan', 'read_only', 1);
        frm.set_df_property('cin', 'read_only', 1);
        frm.set_df_property('bank_account_no', 'read_only', 1);
        frm.set_df_property('bank_ifsc_code', 'read_only', 1);
        frm.set_df_property('udyog_aadhaar', 'read_only', 1);
        frm.set_df_property('phone_number', 'read_only', 1);
        frm.set_df_property('email', 'read_only', 1);
    } else {
        frm.set_df_property('gstn', 'read_only', 0);
        frm.set_df_property('pan', 'read_only', 0);
        frm.set_df_property('cin', 'read_only', 0);
        frm.set_df_property('bank_account_no', 'read_only', 0);
        frm.set_df_property('bank_ifsc_code', 'read_only', 0);
        frm.set_df_property('udyog_aadhaar', 'read_only', 0);
        frm.set_df_property('phone_number', 'read_only', 0);
        frm.set_df_property('email', 'read_only', 0);
    }
}

function send_credentials_manually(frm) {
    frappe.confirm(
        __('This will send a new private onboarding link to {0}. Continue?', [frm.doc.email]),
        function() {
            frappe.call({
                method: 'addsol_vendor_onboarding.addsol_vendor_onboarding.doctype.supplier_onboarding.supplier_onboarding.send_credentials_manually',
                args: {
                    supplier_onboarding: frm.doc.name,
                    force: 1
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __('Private onboarding link sent successfully'),
                            indicator: 'green'
                        });
                    } else {
                        frappe.show_alert({
                            message: __('Failed to send a new private onboarding link'),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    );
}

function reconcile_validation_status(frm) {
    frappe.confirm(
        __('This will recompute validation status from logs for this record. Continue?'),
        function() {
            frappe.call({
                method: 'addsol_vendor_onboarding.api.reconcile_supplier_onboarding_validation_state',
                args: {
                    supplier_onboarding: frm.doc.name
                },
                freeze: true,
                freeze_message: __('Reconciling validation status...'),
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __('Reconciled. Status: {0} / {1}', [
                                r.message.onboarding_status || frm.doc.onboarding_status,
                                r.message.validation_status || frm.doc.validation_status
                            ]),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    } else {
                        frappe.msgprint(__('Unable to reconcile this record. Please check error logs.'));
                    }
                }
            });
        }
    );
}
