frappe.ui.form.on('Supplier Validation Log', {
    refresh: function(frm) {
        // Make the form read-only
        frm.disable_save();
    }
});