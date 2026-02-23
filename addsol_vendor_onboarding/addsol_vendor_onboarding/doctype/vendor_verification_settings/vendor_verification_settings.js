frappe.ui.form.on("Vendor Verification Settings", {
    refresh(frm) {
        set_provider_settings_hint(frm);
    },

    verification_provider(frm) {
        set_provider_settings_hint(frm);
    },
});

function set_provider_settings_hint(frm) {
    const provider = frm.doc.verification_provider || "Cashfree";

    if (provider === "Cashfree") {
        const settings_url = "/app/cashfree-settings";
        frm.fields_dict.provider_settings_hint.$wrapper.html(`
            <div class="small text-muted">
                Configure provider-specific credentials in
                <a href="${settings_url}">Cashfree Settings</a>.
            </div>
        `);
        return;
    }

    if (provider === "Dummy Provider") {
        const settings_url = "/app/dummy-provider-settings";
        frm.fields_dict.provider_settings_hint.$wrapper.html(`
            <div class="small text-muted">
                This provider is a template for future development.
                Configure placeholders in
                <a href="${settings_url}">Dummy Provider Settings</a>.
            </div>
        `);
        return;
    }

    frm.fields_dict.provider_settings_hint.$wrapper.html("");
}
