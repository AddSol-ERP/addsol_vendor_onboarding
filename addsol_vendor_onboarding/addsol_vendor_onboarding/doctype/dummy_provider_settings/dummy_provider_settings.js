frappe.ui.form.on("Dummy Provider Settings", {
    refresh(frm) {
        frm.fields_dict.template_info.$wrapper.html(`
            <div class="small text-muted">
                Template provider for future integrations.
                Implement API methods in
                <code>addsol_vendor_onboarding/api/dummy_provider_api.py</code>
                and replace this DocType with real credentials/flags.
            </div>
        `);

        if (!frm.doc.__islocal) {
            frm.add_custom_button(__("Test Connection"), function() {
                test_dummy_provider_connection();
            });
        }
    },
});

function test_dummy_provider_connection() {
    frappe.call({
        method: "addsol_vendor_onboarding.api.dummy_provider_api.test_connection",
        callback: function(r) {
            const response = r.message || {};
            if (response.success) {
                frappe.show_alert({
                    message: __(response.message || "Dummy provider reachable"),
                    indicator: "green",
                });
            } else {
                frappe.msgprint({
                    title: __("Connection Check"),
                    message: __(response.message || "Dummy provider is a placeholder."),
                    indicator: "orange",
                });
            }
        }
    });
}
