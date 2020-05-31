from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register('projects', ProjectViewSet) # homepage
router.register('project_bug', ProjectBugViewSet, 'project_bug') # project_page, bug_page
router.register('my_page', MyPage, 'my_page') # my_page
router.register('users', UserViewSet) # admin_page

router.register('users', testViewSet)

urlpatterns = router.urls

urlpatterns += [
    path('oauth/redirect/', Auth),

    path('zoo/<enr>', testing.as_view({'get': 'list'})),
    path('test/', testView),
    path('login/', testLogin)
]
