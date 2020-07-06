import requests
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status, generics
from django.contrib.auth import login, logout
from .models import *
from .serializers import *
from .permissions import *

from django.http import HttpResponse
from rest_framework.decorators import action

# Oauth wala view
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def Auth(request):
    client_id = 'er1eJX5UyeQgVLdDLICTjuUJKHogSrLRKfKLLIN9'
    client_secret = 'MQ4fR10F7Mti8aNMhoUKJfznpX6YwCCUffCzqrxHRDLuY9DIOZGgY3q16MVbnbbSFGrGnsXa40qOZB60twj5eK4n1OqMqExmIIOJCn0djXS57k8QAJ5OXPxndKB2E07M'

    # desired_state = 'pypy'

    auth_code = request.query_params.get('code')
    # state = request.query_params.get('state')

    # if (state!=desired_state):
    #     return Response(
    #         data = {'error': 'Something went wrong, please try again later.'},
    #         status = status.HTTP_500_INTERNAL_SERVER_ERROR
    #     )

    url = 'https://internet.channeli.in/open_auth/token/'
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'authorization_code',
        'redirect_url': 'http://localhost:3000/',
        'code': auth_code
    }
    omni_data = requests.post(url=url, data=data).json()

    # checking for any errors
    if ('error' in  omni_data.keys()):
        return Response(
            data = {'error': omni_data['error']},
            status = status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # getting user_data
    access_token = omni_data['access_token']
    refresh_token = omni_data['refresh_token']
    headers = {
        'Authorization': 'Bearer '+access_token
    }
    user_data = requests.get(url='https://internet.channeli.in/open_auth/get_user_data/', headers=headers)

    # checking for any errors
    if (user_data.status_code!=200):
        return Response(
            data = {'error': user_data.json()['detail']},
            status = status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    user = user_data.json()

    # do you already exist?
    try:
        exist = User.objects.get(enrollment_no=user['student']['enrolmentNumber'])
    except:
        pass
    else:
        # here i will check whether this user has send access_token or not and log him/her in
        Response(
            data = {'error': 'You don\'t need to signup, user already exists.', 'acs_token': access_token},
            status = status.HTTP_400_BAD_REQUEST
        )

    # are you an imgian?
    imgian = False
    for role in user['person']['roles']:
        if 'Maintainer' in role.values():
            imgian = True

    if not imgian:
        return Response(
            data = {'error': 'You are not allowed to use this app as you are not an IMGIAN.'},
            status = status.HTTP_401_UNAUTHORIZED
        )
    
    # are you an admin?
    admin_status = False
    if user['student']['currentYear'] > 3:
        admin_status = True

    # creating newUser if everything is fine
    enr_no = user['student']['enrolmentNumber']
    email = user['contactInformation']['instituteWebmailAddress']
    full_name = user['person']['fullName']
    fName = full_name.split()[0]

    try:
        newUser = User(username=full_name, email=email, enrollment_no=enr_no, first_name=fName, admin_status=admin_status, access_token=access_token, refresh_token=refresh_token)
        newUser.save()
    except:
        return Response(
            data = {'error': 'Unable to create account.'},
            status = status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(
        data = {'detail': 'Voila! Account created successfully!', 'access_token': access_token},
        status = status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def AfterLogin(request):
    print('AFTER LOGIN CALLED')
    acs_token = request.query_params.get('acs_token')
    # use refresh_token here if acs_token is invalid
    try:
        user = User.objects.get(access_token=acs_token)
        data = {
            'name': user.username,
            'first_name': user.first_name,
            'admin_status': user.admin_status,
            'disabled_status': user.disabled_status
        }
        # serializer = UserSerializer(user)
        # serializer.is_valid(True)
    except:
        return Response (
            data = {'error': 'User not found OR invalid access token'},
            status = status.HTTP_400_BAD_REQUEST
        )

    return Response(
        data = {'thisUser': data},
        status = status.HTTP_200_OK
    )

# homepage
class ProjectViewSet(ModelViewSet):
    lookup_field = 'name'
    # permission_classes = [CreatorTeamAdminPermission]
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        if ('wiki' in request.data.keys()):
            try:
                assigned_to = User.objects.get(username=request.data['assigned_to'])
                serializer.save(assigned_to_id=assigned_to.id)
            except:
                return Response(
                    data = {'error': 'User doesnot exists'},
                    status = status.HTTP_400_BAD_REQUEST
                )            
        else:
            self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        creator = User.objects.get(username=request.data['creator'])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(creator_id=creator.id)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

# project_page, bug_page
class ProjectBugViewSet(ModelViewSet):
    serializer_class = BugSerializer
    lookup_field = 'heading'
    # permission_classes = [CreatorTeamAdminPermission]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        if ('assigned_to' in request.data.keys()):
            try:
                assigned_to = User.objects.get(username=request.data['assigned_to'])
                serializer.save(assigned_to_id=assigned_to.id)
            except:
                return Response(
                    data = {'error': 'User doesnot exists'},
                    status = status.HTTP_400_BAD_REQUEST
                )            
        else:
            self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        project = Project.objects.get(name=request.data['project'])
        reported_by = User.objects.get(username=request.data['reported_by'])
        
        try:
            assigned_to = User.objects.get(username=request.data['assigned_to'])
            asId = assigned_to.id
        except:
            asId = None

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(project_id=project.id, reported_by_id=reported_by.id, assigned_to_id=asId)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    # function to map project_names to their ids
    def nameMAPpk(self, project_name):
        id = Project.objects.get(name = project_name)
        return id

    def get_queryset(self):
        project_name = self.request.query_params.get('project_name')
        queryset = Bug.objects.filter(project_id = self.nameMAPpk(project_name))
        return queryset

# Bug Viewset

# my_page
class MyPage(ModelViewSet):
    serializer_class = BugSerializer
    # permission_classes = [IsAuthenticated]

    # function to map usernames to their ids
    def nameMAPpk(self, enrollment_no):
        id = User.objects.get(enrollment_no = enrollment_no)
        return id

    def get_queryset(self):
        enrollment_no = self.request.query_params.get('enrollment_no')
        query1 = Bug.objects.filter(reported_by = self.nameMAPpk(enrollment_no))
        query2 = Bug.objects.filter(assigned_to = self.nameMAPpk(enrollment_no))
        return query1 | query2

# admin_page
class UserViewSet(ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    # permission_classes = [AdminPermission]
    lookup_field = 'enrollment_no'
    permission_classes = [AllowAny]

# tags
class TagViewSet(ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()

    def create(self, request, *args, **kwargs):
        creator = User.objects.get(username=request.data['creator'])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(creator_id=creator.id)
        return Response(serializer.data)

    # def create(self, request, *args, **kwargs):
    #     # data = {
    #     #     'name': request.data['name'],
    #     #     'creator': User.objects.get(request.data['creator'])
    #     # }
    #     print('from viewset: '+repr(request.data))
    #     serializer = self.get_serializer(data=request.data)
    #     print(repr(serializer))
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_create(serializer)
    #     headers = self.get_success_headers(serializer.data)
    #     return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


# experimental stuff
class testViewSet(ModelViewSet):
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def testView(request):
    # login(request=request, user=request.user)
    return Response(request.data)

# most important thing that i have learned today
class testing(ModelViewSet):
    serializer_class = UserSerializer
    lookup_url_kwarg = 'enr'

    def get_queryset(self):
        enr = self.kwargs.get(self.lookup_url_kwarg)
        return User.objects.filter(enrollment_no=enr)

@api_view(['GET', 'POST'])
def testLogin(request):
    lg = login(request, user=request.user)
    return Response (
        data=lg
    )
