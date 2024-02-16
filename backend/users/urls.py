from django.urls import include, path

from users import views


urlpatterns = [
  path('', views.Index.as_view(), name='index'),
  path('<int:user_id>/', views.get_user, name='get-user'),
  path('me/', views.me, name='me'),
  path('dfa/', views.DFA.as_view(), name='dfa'),
  path('friends/', include('friends.urls')),
]
