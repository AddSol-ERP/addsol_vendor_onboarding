frappe.listview_settings['Supplier Onboarding'] = {
    add_fields: ["onboarding_status", "validation_status"],
    get_indicator: function(doc) {
        if (doc.onboarding_status === "Approved") {
            return [__("Approved"), "green", "onboarding_status,=,Approved"];
        } else if (doc.onboarding_status === "Rejected") {
            return [__("Rejected"), "red", "onboarding_status,=,Rejected"];
        } else if (doc.onboarding_status === "Validation Successful") {
            return [__("Validation Successful"), "blue", "onboarding_status,=,Validation Successful"];
        } else if (doc.onboarding_status === "Validation Failed") {
            return [__("Validation Failed"), "orange", "onboarding_status,=,Validation Failed"];
        } else if (doc.onboarding_status === "Data Submitted") {
            return [__("Data Submitted"), "yellow", "onboarding_status,=,Data Submitted"];
        } else {
            return [__("Pending Submission"), "gray", "onboarding_status,=,Pending Submission"];
        }
    }
};