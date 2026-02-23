frappe.ready(function () {
    if (window.location.pathname !== "/me") {
        return;
    }

    // Supplier users in this app get a /vendor-portal link in sidebar/menu.
    // If present, hide Edit Profile action on /me.
    var hasVendorPortalLink = Boolean(document.querySelector('a[href="/vendor-portal"]'));
    if (!hasVendorPortalLink) {
        return;
    }

    var editProfileLink = document.querySelector('a[href^="/update-profile/"]');
    if (!editProfileLink) {
        return;
    }

    var container = editProfileLink.closest(".my-account-item-link") || editProfileLink.parentElement;
    if (container) {
        container.style.display = "none";
    }
});
