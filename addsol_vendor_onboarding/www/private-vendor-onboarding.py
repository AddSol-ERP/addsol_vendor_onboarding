"""Public shell; all supplier data requires a valid invitation token."""

def get_context(context):
    context.no_cache = 1
    context.show_sidebar = False
    context.no_breadcrumbs = True
    context.title = "Supplier Onboarding"
