from django.urls import path

from .views import (
    CourseAssignBusView,
    CourseCancelView,
    CourseCreateView,
    CourseListView,
    CourseManageListView,
    CourseNotifyDriverView,
    CourseTransitionView,
    CourseUpdateView,
)

app_name = "intercampus"
urlpatterns = [
    path("", CourseListView.as_view(), name="list"),
    path("manage/", CourseManageListView.as_view(), name="manage"),
    path("new/", CourseCreateView.as_view(), name="create"),
    path("<uuid:pk>/edit/", CourseUpdateView.as_view(), name="update"),
    path("<uuid:pk>/assign-bus/", CourseAssignBusView.as_view(), name="assign_bus"),
    path("<uuid:pk>/notify-driver/", CourseNotifyDriverView.as_view(), name="notify_driver"),
    path("<uuid:pk>/cancel/", CourseCancelView.as_view(), name="cancel"),
    path("<uuid:pk>/<str:target>/", CourseTransitionView.as_view(), name="transition"),
]
