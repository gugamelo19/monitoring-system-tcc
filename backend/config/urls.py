from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/auth/login/", TokenObtainPairView.as_view(),
         name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    path("api/assets/", include("apps.assets.urls")),
    path("api/events/", include("apps.events.urls")),
    path("api/anomalies/", include("apps.anomalies.urls")),
    path("api/alerts/", include("apps.alerts.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
]
