"""
URL configuration for FoodSaver project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, include

urlpatterns = [
    # Include application URLs first so the custom /platform-admin/ dashboard in HungerFree
    # (used for platform administration) takes precedence. Default Django admin
    # is still available at /django-admin/ for site-level management.
    path("", include("HungerFree.urls")),
    path("django-admin/", admin.site.urls),
]
