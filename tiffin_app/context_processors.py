def tenant_context(request):
    """Add tenant branding to all template contexts"""
    context = {
        'tenant': None,
        'theme_primary': '#2c3e50',
        'theme_secondary': '#3498db',
        'theme_accent': '#3498db',
        'logo_url': '/static/tiffin_app/img/default_logo.png',
        'tenant_name': 'Tiffin Service Management',
        'lunch_sticker_color': '#1f2937',
        'dinner_sticker_color': '#111827',
    }
    
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        tenant = request.user.profile.tenant
        context.update({
            'tenant': tenant,
            'theme_primary': tenant.get_primary_color(),
            'theme_secondary': tenant.get_secondary_color(),
            'theme_accent': tenant.get_accent_color(),
            'logo_url': tenant.get_logo_url(),
            'tenant_name': tenant.name,
            'lunch_sticker_color': tenant.get_lunch_sticker_color(),
            'dinner_sticker_color': tenant.get_dinner_sticker_color(),
        })
    
    return context
