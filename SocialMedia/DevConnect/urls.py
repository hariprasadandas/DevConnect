from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/', views.profile, name='profile'),
    path('myposts/', views.myposts, name='myposts'),
    
    path('edit/<int:post_id>/', views.edit_post, name='edit_post'),
    path('delete/<int:post_id>/', views.delete_post, name='delete_post'),
    
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup, name='signup'),
    path('create_post/', views.create_post, name='create_post'),
    path('comment_post/<int:post_id>/', views.comment_post, name='comment_post'),
    path('post/<int:post_id>/comments/', views.comment_post, name='comment_post'),
    path('like_post/<int:post_id>/', views.like_post, name='like_post'),
    
    # ---------------------------API-----------------------------------------
     # Profile APIs
    path('api/profiles/', views.api_profile_list, name='api_profile_list'), #all profile
    
    path('api/profile/', views.api_profile_view, name='api_profile_view'), #logged in user profile
    
    path('api/profile/<str:username>/', views.get_user_profile, name='get_user_profile'),
     
    # path('api/follows/<int:user_id>/', views.api_follow_list, name='api_follow_list'),
    path('api/users/', views.get_users, name='user-list'),   #follow check



    

    # Post APIs
    path('api/posts/', views.api_post_list, name='api_post_list'),
    path('api/posts/<int:pk>/', views.api_post_detail, name='api-post-detail'), #to edit, delete
    path('api/myposts/', views.api_mypost_list, name='api_mypost_list'), #myposts
    
    


    # Like APIs
    path('api/posts/<int:post_id>/like/', views.api_like_post, name='api_like_post'),

    # Comment APIs
    path('api/posts/<int:post_id>/comments/', views.api_comment_list, name='api_comment_list'),

    # Follow APIs
    path('api/follows/<int:user_id>/', views.api_follow_list, name='api_follow_list'),
    
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
