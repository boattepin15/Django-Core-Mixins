from django.urls import path
from core.views.home import (
    DashboardView
)
app_name = "core"

urlpatterns = [
    path('', DashboardView.as_view(), name="dashboard"),
]
