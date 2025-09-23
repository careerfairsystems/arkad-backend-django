"""
URL configuration for arkad project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from .api import api
from .settings import DEBUG, STATIC_URL, STATICFILES_DIRS

# Configure Django Admin with Arkad branding
admin.site.site_header = "Arkad Administration"
admin.site.site_title = "Arkad Admin"
admin.site.index_title = "Welcome to Arkad Administration"
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("user/", include("user_models.urls")),
]

if DEBUG:
    urlpatterns.append(
        path("email/", include("email_app.urls")),
    )
    # In debug also serve the static files
    from django.conf.urls.static import static

    urlpatterns.extend(
        static(STATIC_URL, document_root=STATICFILES_DIRS[0], show_indexes=True)  # type: ignore[arg-type]
    )
