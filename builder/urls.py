from django.urls import path
from . import views
from . import portal_views

urlpatterns = [
    # Auth
    path('login/',  views.login_view,  name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # Bundle custom password reset (not django.contrib.auth.urls)
    path('bundle/password-reset/', views.password_reset_request, name='bundle_password_reset'),
    path(
        'bundle/password-reset/<uuid:token>/',
        views.password_reset_confirm,
        name='bundle_password_reset_confirm',
    ),

    # App
    path('', views.index, name='index'),
    path('chat/new/', views.chat_new, name='chat_new'),
    path('chat/<int:run_id>/', views.chat_thread, name='chat_thread'),
    path('chat/<int:run_id>/report/analysis/', views.report_ai_analysis, name='report_ai_analysis'),
    path('chat/<int:run_id>/report/plan/', views.report_final_plan, name='report_final_plan'),

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

    # PDF download
    path('api/pdf/<int:run_id>/', views.download_pdf, name='download_pdf'),

    # Session-level actions on the final plan report
    path(
        'api/runs/<int:run_id>/employees/<int:emp_idx>/sessions/<int:sess_num>/delete/',
        views.delete_session,
        name='delete_session',
    ),
    path(
        'api/runs/<int:run_id>/employees/<int:emp_idx>/sessions/<int:sess_num>/refine/',
        views.refine_session,
        name='refine_session',
    ),

    # ── Superuser control portal ──────────────────────────────────────────────
    path('control/',                                    portal_views.portal_dashboard,     name='portal_dashboard'),
    path('control/prompts/',                            portal_views.portal_prompts,       name='portal_prompts'),
    path('control/prompts/<str:key>/',                  portal_views.portal_prompt_edit,   name='portal_prompt_edit'),
    path('control/prompts/<str:key>/preview/',          portal_views.portal_prompt_preview, name='portal_prompt_preview'),
    path('control/agents/',                             portal_views.portal_agents,        name='portal_agents'),
    path('control/agents/<int:pk>/save/',               portal_views.portal_agent_save,    name='portal_agent_save'),
    path('control/runs/',                               portal_views.portal_runs,          name='portal_runs'),
]
