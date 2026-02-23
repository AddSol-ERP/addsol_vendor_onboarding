# -*- coding: utf-8 -*-
# Copyright (c) 2025, Addition Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe import _

app_name = "addsol_vendor_onboarding"
app_title = "Addsol Supplier Onboarding"
app_publisher = "Addition Solutions"
app_description = "Supplier onboarding process for new suppliers in India"
app_email = "contact@aitspl.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "addsol_vendor_onboarding",
# 		"logo": "/assets/addsol_vendor_onboarding/logo.png",
# 		"title": "Addsol Vendor Onboarding",
# 		"route": "/addsol_vendor_onboarding",
# 		"has_permission": "addsol_vendor_onboarding.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/addsol_vendor_onboarding/css/addsol_vendor_onboarding.css"
# app_include_js = "/assets/addsol_vendor_onboarding/js/addsol_vendor_onboarding.js"

# include js, css files in header of web template
# web_include_css = "/assets/addsol_vendor_onboarding/css/addsol_vendor_onboarding.css"
# web_include_js = "/assets/addsol_vendor_onboarding/js/addsol_vendor_onboarding.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "addsol_vendor_onboarding/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "addsol_vendor_onboarding/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "addsol_vendor_onboarding.utils.jinja_methods",
# 	"filters": "addsol_vendor_onboarding.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "addsol_vendor_onboarding.install.before_install"
# after_install = "addsol_vendor_onboarding.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "addsol_vendor_onboarding.uninstall.before_uninstall"
# after_uninstall = "addsol_vendor_onboarding.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "addsol_vendor_onboarding.utils.before_app_install"
# after_app_install = "addsol_vendor_onboarding.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "addsol_vendor_onboarding.utils.before_app_uninstall"
# after_app_uninstall = "addsol_vendor_onboarding.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "addsol_vendor_onboarding.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
    "Supplier Onboarding": "addsol_vendor_onboarding.utils.permission_query_conditions.get_supplier_onboarding_conditions"
}

has_permission = {
    "Supplier Onboarding": "addsol_vendor_onboarding.utils.permission_query_conditions.has_supplier_onboarding_permission"
}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

doctype_js = {
    "Purchase Order": "public/js/purchase_order.js",
    "Supplier": "public/js/supplier.js"
}

doc_events = {
    "Purchase Order": {
        "validate": "addsol_vendor_onboarding.api.supplier_portal.validate_purchase_order"
    },
    "Supplier": {
        "before_insert": "addsol_vendor_onboarding.api.supplier_portal.disable_new_supplier",
        "validate": "addsol_vendor_onboarding.api.supplier_portal.validate_supplier_email"
    }
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"addsol_vendor_onboarding.tasks.all"
# 	],
# 	"daily": [
# 		"addsol_vendor_onboarding.tasks.daily"
# 	],
# 	"hourly": [
# 		"addsol_vendor_onboarding.tasks.hourly"
# 	],
# 	"weekly": [
# 		"addsol_vendor_onboarding.tasks.weekly"
# 	],
# 	"monthly": [
# 		"addsol_vendor_onboarding.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "addsol_vendor_onboarding.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "addsol_vendor_onboarding.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "addsol_vendor_onboarding.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["addsol_vendor_onboarding.utils.before_request"]
# after_request = ["addsol_vendor_onboarding.utils.after_request"]

# Job Events
# ----------
# before_job = ["addsol_vendor_onboarding.utils.before_job"]
# after_job = ["addsol_vendor_onboarding.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"addsol_vendor_onboarding.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Configuration for extending Buying module
extend_bootinfo = "addsol_vendor_onboarding.boot.boot_session"

# Add links to other modules
# This will add Vendor Onboarding items to Buying workspace
additional_timeline_content = {
    "Supplier": ["addsol_vendor_onboarding.addsol_vendor_onboarding.doctype.supplier_onboarding.supplier_onboarding.get_timeline_data"]
}
