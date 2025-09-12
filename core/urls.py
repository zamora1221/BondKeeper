
from django.urls import path
from . import views_people as views

urlpatterns = [
    path('', views.people_home, name='people_home'),
    path('tab/list/', views.people_tab_list, name='people_tab_list'),
    path('tab/main/<int:pk>/', views.person_main_panel, name='people_tab_main'),
    path('new/partial/', views.person_new_partial, name='person_new_partial'),
    path('edit/<int:pk>/', views.person_edit_partial, name='person_edit_partial'),
    path('save/<int:pk>/', views.person_save_partial, name='person_save_partial'),
    path('indemnitors/new/<int:person_pk>/', views.indemnitor_new_partial, name='indemnitor_new_partial'),
    path('references/new/<int:person_pk>/', views.reference_new_partial, name='reference_new_partial'),
    path('indemnitors/<int:pk>/edit/', views.indemnitor_edit_partial, name='indemnitor_edit_partial'),
    path('references/<int:pk>/edit/', views.reference_edit_partial, name='reference_edit_partial'),
# Indemnitors
    path("people/<int:person_pk>/indemnitors/new/partial/", views.indemnitor_new_partial, name="indemnitor_new_partial"),
    path("indemnitors/<int:pk>/edit/partial/", views.indemnitor_edit_partial, name="indemnitor_edit_partial"),
    path("people/indemnitors/<int:pk>/delete/", views.indemnitor_delete, name="indemnitor_delete"),
    path("people/references/<int:pk>/delete/",  views.reference_delete,  name="reference_delete"),
    # References
    path("people/<int:person_pk>/references/new/partial/", views.reference_new_partial, name="reference_new_partial"),
    path("references/<int:pk>/edit/partial/", views.reference_edit_partial, name="reference_edit_partial"),
    # Court Dates
    path("people/<int:person_pk>/court-dates/new/partial/", views.court_date_new_partial, name="court_date_new_partial"),
    path("court-dates/<int:pk>/edit/partial/",            views.court_date_edit_partial, name="court_date_edit_partial"),
    path("people/court-dates/<int:pk>/delete/",            views.court_date_delete,       name="court_date_delete"),
    path("people/<int:person_pk>/court-dates/recent/partial/", views.court_date_recent_widget, name="court_date_recent_widget"),
    # Bonds
    path("people/<int:person_pk>/bonds/new/partial/", views.bond_new_partial, name="bond_new_partial"),
    path("bonds/<int:pk>/edit/partial/", views.bond_edit_partial, name="bond_edit_partial"),
    path("people/bonds/<int:pk>/delete/", views.bond_delete, name="bond_delete"),
    path("people/<int:person_pk>/checkins/new/partial/", views.checkin_new_partial, name="checkin_new_partial"),
    path("checkins/<int:pk>/edit/partial/",              views.checkin_edit_partial, name="checkin_edit_partial"),
    path("people/checkins/<int:pk>/delete/",             views.checkin_delete,       name="checkin_delete"),
    path("people/<int:person_pk>/checkins/last/partial/",views.checkin_last_widget,name="checkin_last_widget",),
    # Invoices
    path("people/<int:person_pk>/invoices/new/partial/", views.invoice_new_partial, name="invoice_new_partial"),
    path("invoices/<int:pk>/edit/partial/",              views.invoice_edit_partial, name="invoice_edit_partial"),
    path("people/invoices/<int:pk>/delete/",             views.invoice_delete,       name="invoice_delete"),
    path("people/<int:person_pk>/invoices/section/partial/",views.invoices_section_partial,name="invoices_section_partial",),

    # Receipts
    path("invoices/<int:invoice_pk>/receipts/new/partial/", views.receipt_new_partial, name="receipt_new_partial"),
    path("receipts/<int:pk>/edit/partial/",                 views.receipt_edit_partial, name="receipt_edit_partial"),
    path("people/receipts/<int:pk>/delete/",                views.receipt_delete,       name="receipt_delete"),
    path("people/<int:person_pk>/receipts/new/partial/",    views.receipt_new_for_person_partial, name="receipt_new_for_person_partial"),
    path("people/<int:person_pk>/billing/summary/partial/",views.billing_summary_widget,name="billing_summary_widget",),

    # Court date printable notice
    path("court-dates/<int:pk>/notice/", views.court_date_notice, name="court_date_notice"),

    # Receipt printable
    path("receipts/<int:pk>/print/", views.receipt_print, name="receipt_print"),


]
