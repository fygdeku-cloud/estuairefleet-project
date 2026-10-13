from django.urls import path

from .views import CourseCreateView, CourseListView, CourseManageListView, CourseTransitionView

app_name = "intercampus"
urlpatterns = [
    path("", CourseListView.as_view(), name="list"),
    path("manage/", CourseManageListView.as_view(), name="manage"),
    path("new/", CourseCreateView.as_view(), name="create"),
    path("<uuid:pk>/<str:target>/", CourseTransitionView.as_view(), name="transition"),
]
