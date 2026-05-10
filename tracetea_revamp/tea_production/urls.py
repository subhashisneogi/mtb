
"""
Tea Production Urls (URLs)
"""

from django.conf.urls import url
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'tea_production'

urlpatterns = [
    url(r'^tea-grade/list/', views.TeaGradeListView.as_view(), name='tea_grade_list'),
    url(r'^tea-grade/create/', views.TeaGradeCreateView.as_view(),
         name='tea_grade_create'), 

    url(r'^tea-grade/edit/(?P<tea_grade_pk>\d+)/$',
        views.TeaGradeUpdateView.as_view(), name='tea_grade_update'),

    url(r'^tea-grade/delete/(?P<tea_grade_pk>\d+)/delete/$',
        views.TeaGradeDeleteView, name='tea_grade_delete'),

    url(r'^tea-grade/search/',
        views.search_tea_grade, name='search_tea_grade'),    

    url(r'^tea-grade/details/(?P<tea_grade_pk>\d+)/$',
        views.grade_details, name='tea_grade_details'),

]