"""
Urls
"""
from django.conf.urls import url
from . import views

app_name = 'gardens_managment'

urlpatterns = [

    url(r'^tea-garden/list/(?P<grower_pk>\d+)/$', views.GardenLisView.as_view(), name='garden_list'),

    url(r'^tea-garden/create/(?P<grower_pk>\d+)/$', views.GardenCreateView.as_view(), name='garden_create'),
    
    url(r'^tea-garden/update/(?P<garden_pk>\d+)/(?P<grower_pk>\d+)/$', views.GardenDetailsUpdateView.as_view(),
         name='garden_update'),
    url(r'^tea-garden/delete/(?P<garden_pk>\d+)/$', views.garden_delete, name='garden_delete'),

    url(r'^tea-garden/details/(?P<grower_pk>\d+)/$', views.garden_details_view, name='garden_details'),



# #######################  ESTATE ######################
    url(r'^garden/details/(?P<user_pk>\d+)/$', views.user_garden_details_view, name='user_garden_details'),
    url(r'^garden/update/(?P<garden_pk>\d+)/(?P<user_pk>\d+)/$', views.GardenUpdateView.as_view(),
         name='user_garden_update'),
    url(r'^garden/division/create/(?P<garden_pk>\d+)/$', views.EstateDivisionCreateView.as_view(), name='estate_division_create'),
    url(r'^garden/division/update/(?P<garden_pk>\d+)/(?P<division_pk>\d+)/$', views.UserDivisionDetailsUpdateView.as_view(), name='user_division_update'),
    

    # Division
    url(r'^tea-garden/division/list/(?P<garden_pk>\d+)/$', views.DivisionLisView.as_view(), name='division_list'),
    url(r'^tea-garden/division/create/(?P<garden_pk>\d+)/$', views.DivisionCreateView.as_view(), name='division_create'),
    url(r'^tea-garden/division/update/(?P<garden_pk>\d+)/(?P<division_pk>\d+)/$', views.DivisionDetailsUpdateView.as_view(), name='division_update'),
    url(r'^tea-garden/division/delete/(?P<division_pk>\d+)/$', views.division_delete, name='division_delete'),
    url(r'^tea-garden/search/', views.sesarch_garden, name='garden_search'),



    url(r'^tea-garden/divisiopn/section/(?P<division_pk>\d+)/(?P<garden_pk>\d+)/$', views.section_details, name='section_details'),
    url(r'^garden/divisiopn/section/list/(?P<division_pk>\d+)/(?P<garden_pk>\d+)/$', views.user_section_details, name='user_section_details'),
]


