"""
Urls
"""
from django.conf.urls import url
from . import views

app_name = 'invoicing'

urlpatterns = [

    url(r'^invoice/list/', views.InvoiceListView.as_view(), name='invoice_list'),
    url(r'^invoice/create/', views.InvoiceCreateView.as_view(),
         name='invoice_create'), 
    url(r'^invoice/edit/(?P<invoice_pk>\d+)/$',
        views.InvoiceUpdateView.as_view(), name='invoice_update'),
    url(r'^invoice/delete/(?P<invoice_pk>\d+)/delete/$',
        views.invoice_delete, name='invoice_delete'),


    # url(r'^invoice/details/(?P<invoice_pk>\d+)/$',
    #     views.invoice_view, name='invoice_details'),
    url(r'^invoice/load_range/$', views.load_range, name='load_range'),
        
    #Reports
    url(r'^reports/invoice-register-list/', views.invoice_register_reports, name='invoice_register_reports'),
    url(r'^reports/backward-traceability-list/', views.backward_traceability_report, name='backward_traceability_report'),
   
    url(r'^reports/backward-traceability-details/(?P<id>\d+)/$', views.backward_traceability_details, name='backward_traceability_details'),
    url(r'^reports/backward-traceability-details/admin/(?P<id>\d+)/(?P<entity_id>\d+)/$', views.admin_backward_traceability_details, name='admin_backward_traceability_details'),


    url(r'^reports/backward-traceability-details/pdf/(?P<id>\d+)/$', views.backward_traceability_details_pdf, name='backward_traceability_details_pdf'),





    # FORWARD
    url(r'^reports/forward-traceability-list/', views.forward_traceability_report, name='forward_traceability_report'),

    url(r'^reports/forward-traceability/pdf/downlaod/', views.forward_reports_pdf, name='forward_reports_pdf'),
    
    
    # REPORTS PDF BLF
    url(r'^reports/invoice-register-pdf/', views.invoice_register_reports_pdf, name='invoice_register_reports_pdf'),

    # ADMIN REPORTS

    url(r'^reports/invoice-register/admin/', views.invoice_register_reports_admin, name='invoice_register_reports_admin'),
    
    url(r'^reports/invoice-register/reports/pdf/admin/', views.invoice_register_reports_pdf_admin, name='invoice_register_reports_pdf_admin'),
]


