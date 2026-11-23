def site_theme(request):
    """Expose the current theme to templates.

    - If user is authenticated, use their saved `theme`.
    - Otherwise fall back to the `site_theme` cookie or 'light'.
    """
    try:
        if getattr(request, 'user', None) and request.user.is_authenticated:
            theme = getattr(request.user, 'theme', 'light')
        else:
            theme = request.COOKIES.get('site_theme', 'light')
    except Exception:
        theme = 'light'
    return {'site_theme': theme}
