from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/',  views.login_view,  name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # App
    path('', views.index, name='index'),

    # API
    path('api/start/',                views.start_chat,   name='start_chat'),
    path('api/new/',                  views.new_run,       name='new_run'),
    path('api/chat/',                 views.chat,          name='chat'),
    path('api/upload/<int:run_id>/',  views.upload_file,   name='upload_file'),
    path('api/book/<int:run_id>/',    views.book,          name='book'),

    # Threads
    path('threads/load/<int:run_id>/', views.load_thread, name='load_thread'),

    # Confirmation
    path('confirm/<int:run_id>/', views.confirm, name='confirm'),
]
