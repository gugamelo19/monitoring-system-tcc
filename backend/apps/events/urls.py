from rest_framework.routers import DefaultRouter
from .views import NetworkEventViewSet

router = DefaultRouter()
router.register(r"", NetworkEventViewSet, basename="events")

urlpatterns = router.urls
