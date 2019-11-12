from django.conf.urls import url
from django.utils.decorators import method_decorator

from cart.utils import after_login
from . import views
from rest_framework_jwt.views import obtain_jwt_token, ObtainJSONWebToken
from rest_framework.routers import DefaultRouter

urlpatterns = [
    url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameView.as_view()),
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileView.as_view()),
    url(r'^user/$', views.UserDetailView.as_view()),
    url(r'^users/$', views.UserCreateView.as_view()),
    # url(r'^authorizations/$', obtain_jwt_token),
    url(r'^authorizations/$', method_decorator(after_login,name='post')(ObtainJSONWebToken).as_view()),
    url(r'^email/$', views.EmailView.as_view()),
    url(r'^emails/verification/$', views.VerifyEmailView.as_view()),
    url(r'^browse_histories/$', views.UserBrowsingHistoryView.as_view()),
]

router = DefaultRouter()
router.register('addresses', views.AddressUserView, base_name="address")
urlpatterns += router.urls