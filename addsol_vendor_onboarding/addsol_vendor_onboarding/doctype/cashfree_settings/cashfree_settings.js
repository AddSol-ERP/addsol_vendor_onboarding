const SANDBOX_API_URL = "https://sandbox.cashfree.com/verification";
const PRODUCTION_API_URL = "https://api.cashfree.com/verification";

frappe.ui.form.on("Cashfree Settings", {
    refresh(frm) {
        // Add a test connection button
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__("Test Connection"), function() {
                test_cashfree_connection(frm);
            });
        }
    },

    is_sandbox(frm) {
        frm.set_value("api_url", frm.doc.is_sandbox ? SANDBOX_API_URL : PRODUCTION_API_URL);
    },

    validate(frm) {
        const disabled = [];
        if (!frm.doc.enable_gstn_validation) disabled.push(__("GSTN"));
        if (!frm.doc.enable_pan_validation) disabled.push(__("PAN"));
        if (!frm.doc.enable_bank_validation) disabled.push(__("Bank Account"));

        if (disabled.length) {
            frappe.msgprint({
                title: __("Strong Warning"),
                message: __(
                    "Mandatory validations are disabled: {0}. Supplier verification can be blocked or produce incomplete outcomes.",
                    [disabled.join(", ")]
                ),
                indicator: "orange",
            });
        }
    },
});

function test_cashfree_connection(frm) {
    frappe.call({
        method: 'addsol_vendor_onboarding.api.cashfree_api.test_connection',
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __('Connection successful!'),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint({
                    title: __('Connection Failed'),
                    message: r.message ? r.message.message : __('Failed to connect to Cashfree API'),
                    indicator: 'red'
                });
            }
        }
    });
}
