# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from frappe import _


def get_context(context):
    context.title = _("Purchase Manager User Manual")
    context.no_cache = 1
    context.show_sidebar = False
    return context
