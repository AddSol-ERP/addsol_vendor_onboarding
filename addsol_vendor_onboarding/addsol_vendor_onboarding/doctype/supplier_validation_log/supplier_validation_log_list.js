frappe.listview_settings["Supplier Validation Log"] = {
    add_fields: ["status", "validation_type", "validation_datetime"],
    get_indicator(doc) {
        if (doc.status === "Success") {
            return [__("Success"), "green", "status,=,Success"];
        }
        if (doc.status === "Failed") {
            return [__("Failed"), "red", "status,=,Failed"];
        }
        return [__("Pending"), "orange", "status,=,Pending"];
    },
};

