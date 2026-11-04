frappe.pages["vendor-onboarding-help"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Supplier Onboarding User Guide"),
		single_column: false,
	});

	page.main.empty().html(`
		<style>
			.vo-help { display: flex; gap: 16px; align-items: flex-start; }
			.vo-help-sidebar { flex: 0 0 260px; position: sticky; top: 16px; max-height: calc(100vh - 140px); overflow: auto; }
			.vo-help-content { flex: 1; min-width: 0; }
			.vo-help-search { margin-bottom: 10px; }
			.vo-help-nav .doc-item { display: block; width: 100%; text-align: left; border: 0; background: transparent; padding: 7px 9px; border-radius: 6px; color: var(--text-color); font-size: 13px; cursor: pointer; }
			.vo-help-nav .doc-item:hover { background: var(--subtle-fg); }
			.vo-help-nav .doc-item.active { background: var(--blue-50); color: var(--blue-700); font-weight: 600; }
			.vo-help-toolbar { display: flex; justify-content: flex-end; margin-bottom: 8px; }
			.vo-help-sections { display: flex; gap: 5px; flex-wrap: wrap; justify-content: flex-start; margin-right: auto; }
			.vo-help-sections .sect-link { font-size: 11px; padding: 3px 8px; border-radius: 10px; background: var(--subtle-fg); color: var(--text-muted); cursor: pointer; }
			.vo-help-body .frappe-card { padding: 24px 28px; }
			.vo-help-body h1 { font-size: 1.6rem; margin: 0 0 8px; }
			.vo-help-body h2 { font-size: 1.25rem; margin-top: 28px; }
			.vo-help-body h3 { font-size: 1.05rem; margin-top: 20px; }
			.vo-help-body table { width: 100%; margin: 12px 0; }
			.vo-help-body pre { background: var(--gray-900); color: var(--gray-100); padding: 14px 16px; border-radius: 8px; overflow: auto; font-size: 12px; line-height: 1.5; }
			.vo-help-body code { background: var(--subtle-fg); padding: 1px 5px; border-radius: 4px; }
			.vo-help-body pre code { background: transparent; padding: 0; }
			.vo-help-empty { color: var(--text-muted); padding: 40px 0; text-align: center; }
			@media (max-width: 900px) { .vo-help { display: block; } .vo-help-sidebar { position: static; max-height: none; margin-bottom: 16px; } }
			@media print { .vo-help-sidebar, .vo-help-toolbar, .navbar, .layout-side-section { display: none !important; } .vo-help-content { width: 100% !important; } .frappe-card { box-shadow: none !important; border: 0 !important; } }
		</style>
		<div class="vo-help">
			<aside class="vo-help-sidebar">
				<div class="vo-help-search"><input class="form-control" type="search" placeholder="${__("Search guides…")}"></div>
				<nav class="vo-help-nav"></nav>
			</aside>
			<section class="vo-help-content">
				<div class="vo-help-toolbar">
					<div class="vo-help-sections"></div>
					<button class="btn btn-default btn-sm" data-help-role="print">${__("Print")}</button>
				</div>
				<div class="vo-help-body"><div class="frappe-card"><div class="vo-help-empty">${__("Loading…")}</div></div></div>
			</section>
		</div>
	`);

	const $nav = page.main.find(".vo-help-nav");
	const $body = page.main.find(".vo-help-body");
	const $sections = page.main.find(".vo-help-sections");
	const $search = page.main.find(".vo-help-search input");
	let items = [];
	let activeRoute = null;

	function routeFromHash() {
		const route = decodeURIComponent((window.location.hash || "").replace(/^#/, "")).replace(/^\/+/, "");
		return items.some((item) => item.route === route) ? route : null;
	}

	function renderDocument(document) {
		$body.html('<div class="frappe-card">' + document.html + "</div>");
		$sections.empty();
		$body.find("h2, h3").each(function () {
			const $heading = $(this);
			const id = $heading.attr("id") || "";
			if (!id) return;
			$heading.css("scroll-margin-top", "20px");
			$sections.append(`<button type="button" class="btn btn-xs sect-link" data-target="${frappe.utils.escape_html(id)}">${frappe.utils.escape_html($heading.text())}</button>`);
		});
	}

	function openDocument(route) {
		if (!route) return;
		activeRoute = route;
		if (window.history && window.history.replaceState) window.history.replaceState(null, "", "#" + route);
		$nav.find(".doc-item").removeClass("active");
		$nav.find(`.doc-item[data-route="${route}"]`).addClass("active");
		$sections.empty();
		$body.html('<div class="frappe-card"><div class="vo-help-empty">' + __("Loading…") + "</div></div>");
		frappe.call({
			method: "addsol_vendor_onboarding.addsol_vendor_onboarding.page.vendor_onboarding_help.vendor_onboarding_help.get_markdown",
			args: { route },
			callback: function (response) {
				if (response.message && response.message.html) renderDocument(response.message);
				else $body.html('<div class="frappe-card"><div class="vo-help-empty">' + __("Document not found.") + "</div></div>");
			},
		});
	}

	function renderNavigation() {
		const query = ($search.val() || "").trim().toLowerCase();
		const matches = items.filter((item) => !query || item.title.toLowerCase().includes(query) || item.route.toLowerCase().includes(query));
		$nav.empty();
		matches.forEach((item) => {
			const active = item.route === activeRoute ? "active" : "";
			$nav.append(`<button type="button" class="doc-item ${active}" data-route="${frappe.utils.escape_html(item.route)}">${frappe.utils.escape_html(item.title)}</button>`);
		});
		if (!matches.length) $nav.html('<div class="vo-help-empty">' + __("No matching guides") + "</div>");
	}

	page.main.find("[data-help-role=print]").on("click", () => window.print());
	$nav.on("click", ".doc-item", function () { openDocument($(this).attr("data-route")); });
	$sections.on("click", ".sect-link", function () {
		const target = document.getElementById($(this).attr("data-target"));
		if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
	});
	$search.on("input", renderNavigation);
	window.addEventListener("hashchange", () => {
		const route = routeFromHash();
		if (route && route !== activeRoute) openDocument(route);
	});

	frappe.call({
		method: "addsol_vendor_onboarding.addsol_vendor_onboarding.page.vendor_onboarding_help.vendor_onboarding_help.get_toc",
		callback: function (response) {
			items = (response.message && response.message.items) || [];
			renderNavigation();
			openDocument(routeFromHash() || (response.message && response.message.default_route) || "Purchase_Manager_User_Manual");
		},
	});
};
