
import json
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Person, Indemnitor, Reference, Bond, CourtDate, CheckIn, Invoice, Receipt
from .forms import PersonForm, IndemnitorForm, ReferenceForm, BondForm, CourtDateForm, CheckInForm, InvoiceForm, ReceiptForm
from .utils import get_current_tenant
from decimal import Decimal
from django.db.models import Sum, Max
from django.utils import timezone
from datetime import datetime
import logging

log = logging.getLogger(__name__)

def tab_main(request, pk):
    try:
        person = get_object_or_404(Person, pk=pk)
        q = (request.GET.get("q") or "").strip()
        # ... rest of your logic ...
        return render(request, "tabs/main.html", {"person": person, "q": q})
    except Exception:
        log.exception("tab_main crashed for pk=%s", pk)
        return HttpResponse("Server error", status=500)
        
@login_required
def people_home(request):
    return render(request, 'people/home.html', {})

@login_required
def people_tab_list(request):
    q = request.GET.get('q', '').strip()
    qs = Person.objects.filter(tenant=request.tenant)
    if q:
        qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q))
    return render(request, 'people/_list.html', {'people': qs.order_by('last_name','first_name')[:200]})

def person_main_panel(request, pk):
    tenant = get_current_tenant(request)
    person = get_object_or_404(Person, pk=pk, tenant=tenant)
    invoice_rows, invoice_totals = _invoice_context(person)
    receipt_list = _receipts_for_person(person)
    return render(request, "people/_tab_main.html", {
        "person": person,
        "invoice_rows": invoice_rows,
        "invoice_totals": invoice_totals,
        "receipt_list": receipt_list,
    })


@login_required
def person_new_partial(request):
    tenant = get_current_tenant(request)
    if request.method == "POST":
        form = PersonForm(request.POST)
        if form.is_valid():
            person = form.save(commit=False)
            person.tenant = tenant
            person.save()
            # Return the main tab for the new person and trigger list refresh + auto-select + close modal
            resp = render(request, "people/_tab_main.html", {"person": person})
            resp["HX-Trigger"] = json.dumps({
                "people_list_refresh": True,
                "people_select": {"pk": person.pk},
                "modal_close": True,
            })
            return resp
        # invalid POST -> re-render form as NEW so it posts to the create URL
        return render(request, "people/_form_person.html", {"form": form, "is_new": True}, status=400)

    # GET -> empty form as NEW
    form = PersonForm()
    return render(request, "people/_form_person.html", {"form": form, "is_new": True})

@login_required
def person_edit_partial(request, pk):
    person = get_object_or_404(Person, pk=pk, tenant=request.tenant)
    form = PersonForm(instance=person)
    return render(request, 'people/_form_person.html', {'form': form, 'person': person, 'is_new': False})

@login_required
def person_save_partial(request, pk):
    tenant = get_current_tenant(request)
    person = get_object_or_404(Person, pk=pk, tenant=tenant)
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    form = PersonForm(request.POST, instance=person)
    if form.is_valid():
        person = form.save()
        resp = render(request, "people/_tab_main.html", {"person": person})
        resp["HX-Trigger"] = json.dumps({
            "people_list_refresh": True,
            "people_select": {"pk": person.pk},
            "modal_close": True,
        })
        return resp

    # invalid edit -> render as EDIT (is_new=False) so it posts to the save URL with pk
    return render(request, "people/_form_person.html", {"form": form, "person": person, "is_new": False}, status=400)

# --- Indemnitors ---
@login_required
def indemnitor_new_partial(request, person_pk):
    tenant = get_current_tenant(request)
    person = get_object_or_404(Person, pk=person_pk, tenant=tenant)
    if request.method == "POST":
        form = IndemnitorForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.person = person
            obj.tenant = tenant
            obj.save()
            # ⬇️ Only return the section (not the whole tab)
            resp = render(request, "people/_section_indemnitors.html", {"person": person})
            resp["HX-Trigger"] = json.dumps({"modal_close": True})
            return resp
        return render(request, "people/_form_indemnitor.html", {"form": form, "person": person})
    form = IndemnitorForm()
    return render(request, "people/_form_indemnitor.html", {"form": form, "person": person})

@login_required
def indemnitor_edit_partial(request, pk):
    tenant = get_current_tenant(request)
    obj = get_object_or_404(Indemnitor, pk=pk, tenant=tenant)
    person = obj.person
    if request.method == "POST":
        form = IndemnitorForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            resp = render(request, "people/_section_indemnitors.html", {"person": person})
            resp["HX-Trigger"] = json.dumps({"modal_close": True})
            return resp
        return render(request, "people/_form_indemnitor.html", {"form": form, "person": person, "indemnitor": obj})
    form = IndemnitorForm(instance=obj)
    return render(request, "people/_form_indemnitor.html", {"form": form, "person": person, "indemnitor": obj})

@login_required
def indemnitor_delete(request, pk):
    ind = get_object_or_404(Indemnitor, pk=pk)
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    person = ind.person
    ind.delete()
    return render(request, "people/_section_indemnitors.html", {"person": person})

# --- References ---
@login_required
def reference_new_partial(request, person_pk):
    tenant = get_current_tenant(request)
    person = get_object_or_404(Person, pk=person_pk, tenant=tenant)
    if request.method == "POST":
        form = ReferenceForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.person = person
            obj.tenant = tenant
            obj.save()
            # ⬇️ Only return the section (not the whole tab)
            resp = render(request, "people/_section_references.html", {"person": person})
            resp["HX-Trigger"] = json.dumps({"modal_close": True})
            return resp
        return render(request, "people/_form_reference.html", {"form": form, "person": person})
    form = ReferenceForm()
    return render(request, "people/_form_reference.html", {"form": form, "person": person})

@login_required
def reference_edit_partial(request, pk):
    tenant = get_current_tenant(request)
    obj = get_object_or_404(Reference, pk=pk, tenant=tenant)
    person = obj.person
    if request.method == "POST":
        form = ReferenceForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            resp = render(request, "people/_section_references.html", {"person": person})
            resp["HX-Trigger"] = json.dumps({"modal_close": True})
            return resp
        return render(request, "people/_form_reference.html", {"form": form, "person": person, "reference": obj})
    form = ReferenceForm(instance=obj)
    return render(request, "people/_form_reference.html", {"form": form, "person": person, "reference": obj})

@login_required
def reference_delete(request, pk):
    ref = get_object_or_404(Reference, pk=pk)
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    person = ref.person
    ref.delete()
    return render(request, "people/_section_references.html", {"person": person})


@login_required
def bond_new_partial(request, person_pk):
    tenant = get_current_tenant(request)
    person = get_object_or_404(Person, pk=person_pk, tenant=tenant)
    if request.method == "POST":
        form = BondForm(request.POST)
        if form.is_valid():
            bond = form.save(commit=False)
            bond.person = person
            bond.tenant = tenant
            bond.save()

            # ---- AUTO-INVOICE HERE (no signals) ----
            amount = bond.bond_amount or Decimal("0")
            if amount > 0:
                inv_number = f"BOND-{bond.pk}"
                # avoid duplicates on accidental resubmits
                inv, created = Invoice.objects.get_or_create(
                    tenant=tenant,
                    person=person,
                    number=inv_number,
                    defaults={
                        "date": bond.date or timezone.localdate(),
                        "description": f"Bond for {getattr(bond, 'offense_type', '') or 'Offense'}",
                        "amount": amount,
                        "due_date": getattr(bond, "date", None),
                        "status": Invoice.STATUS_UNPAID,
                    },
                )
                # if you want to update the amount when an existing invoice is found:
                # if not created and inv.amount != amount:
                #     inv.amount = amount
                #     inv.save(update_fields=["amount"])

            # Return the bonds section; also tell widgets to refresh
            resp = render(request, "people/_section_bonds.html", {"person": person})
            resp["HX-Trigger"] = json.dumps({"modal_close": True, "billing_changed": True})
            return resp

        return render(request, "people/_form_bond.html", {"form": form, "person": person})

    form = BondForm()
    return render(request, "people/_form_bond.html", {"form": form, "person": person})


@login_required
def bond_edit_partial(request, pk):
    tenant = get_current_tenant(request)
    obj = get_object_or_404(Bond, pk=pk, tenant=tenant)
    person = obj.person
    if request.method == "POST":
        form = BondForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            resp = render(request, "people/_section_bonds.html", {"person": person})
            resp['HX-Trigger'] = json.dumps({'modal_close': True})
            return resp
        return render(request, "people/_form_bond.html", {"form": form, "person": person, "bond": obj})
    form = BondForm(instance=obj)
    return render(request, "people/_form_bond.html", {"form": form, "person": person, "bond": obj})

@login_required
def bond_delete(request, pk):
    b = get_object_or_404(Bond, pk=pk)
    if hasattr(request.user, "tenant_id") and getattr(b, "tenant_id", None) != request.user.tenant_id:
        return HttpResponse(status=403)
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    person = b.person
    b.delete()
    return render(request, "people/_section_bonds.html", {"person": person})

@login_required
def court_date_new_partial(request, person_pk):
    tenant = get_current_tenant(request)
    person = get_object_or_404(Person, pk=person_pk, tenant=tenant)
    if request.method == "POST":
        form = CourtDateForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.person = person
            obj.tenant = tenant
            obj.save()
            resp = render(request, "people/_section_court_dates.html", {"person": person})
            resp["HX-Trigger"] = json.dumps({"modal_close": True, "court_dates_changed": True})
            return resp
        return render(request, "people/_form_court_date.html", {"form": form, "person": person})
    form = CourtDateForm()
    return render(request, "people/_form_court_date.html", {"form": form, "person": person})

@login_required
def court_date_edit_partial(request, pk):
    tenant = get_current_tenant(request)
    obj = get_object_or_404(CourtDate, pk=pk, tenant=tenant)
    person = obj.person
    if request.method == "POST":
        form = CourtDateForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            resp = render(request, "people/_section_court_dates.html", {"person": person})
            resp["HX-Trigger"] = json.dumps({"modal_close": True, "court_dates_changed": True})
            return resp
        return render(request, "people/_form_court_date.html", {"form": form, "person": person, "court_date": obj})
    form = CourtDateForm(instance=obj)
    return render(request, "people/_form_court_date.html", {"form": form, "person": person, "court_date": obj})

@login_required
def court_date_delete(request, pk):
    cd = get_object_or_404(CourtDate, pk=pk)
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    person = cd.person
    cd.delete()
    return render(request, "people/_section_court_dates.html", {"person": person})

def _recent_court_date(person):
    return person.court_dates.order_by('-date', '-time', '-id').first()

# widget view
@login_required
def court_date_recent_widget(request, person_pk):
    tenant = get_current_tenant(request)
    person = get_object_or_404(Person, pk=person_pk, tenant=tenant)
    cd = _recent_court_date(person)
    return render(request, "people/_widget_recent_court_date.html", {
        "person": person,
        "recent_cd": cd,
    })

@login_required
def court_date_notice(request, pk):
    tenant = get_current_tenant(request)
    cd = get_object_or_404(
        CourtDate.objects.select_related("person"),
        pk=pk,
        person__tenant=tenant,
    )
    person = cd.person
    return render(request, "people/print_court_notice.html", {
        "person": person,
        "court_date": cd,
        "tenant": tenant,
    })

@login_required
def checkin_new_partial(request, person_pk):
    tenant = get_current_tenant(request)
    person = get_object_or_404(Person, pk=person_pk, tenant=tenant)
    if request.method == "POST":
        form = CheckInForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.person = person
            obj.tenant = tenant
            obj.save()
            resp = render(request, "people/_section_checkins.html", {"person": person})
            resp["HX-Trigger"] = json.dumps({"modal_close": True, "checkins_changed": True})
            return resp
        return render(request, "people/_form_checkin.html", {"form": form, "person": person})
    form = CheckInForm()
    return render(request, "people/_form_checkin.html", {"form": form, "person": person})

@login_required
def checkin_edit_partial(request, pk):
    tenant = get_current_tenant(request)
    obj = get_object_or_404(CheckIn, pk=pk, tenant=tenant)
    person = obj.person
    if request.method == "POST":
        form = CheckInForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            resp = render(request, "people/_section_checkins.html", {"person": person})
            resp["HX-Trigger"] = json.dumps({"modal_close": True, "checkins_changed": True})
            return resp
        return render(request, "people/_form_checkin.html", {"form": form, "person": person, "checkin": obj})
    form = CheckInForm(instance=obj)
    return render(request, "people/_form_checkin.html", {"form": form, "person": person, "checkin": obj})

@login_required
def checkin_delete(request, pk):
    ci = get_object_or_404(CheckIn, pk=pk)
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    person = ci.person
    ci.delete()
    return render(request, "people/_section_checkins.html", {"person": person})

@login_required
def checkin_last_widget(request, person_pk):
    tenant = get_current_tenant(request)
    person = get_object_or_404(Person, pk=person_pk, tenant=tenant)

    last_ci = CheckIn.objects.filter(person=person, tenant=tenant)\
                             .order_by('-created_at', '-id').first()

    days_since = None
    last_date = None
    if last_ci and last_ci.created_at:
        last_date = timezone.localdate(last_ci.created_at)
        days_since = (timezone.localdate() - last_date).days

    return render(request, "people/_widget_last_checkin.html", {
        "person": person,
        "days_since": days_since,
        "last_date": last_date,  # optional, if you want to show the date on hover, etc.
    })

@login_required
def invoice_new_partial(request, person_pk):
    tenant = get_current_tenant(request)
    person = get_object_or_404(Person, pk=person_pk, tenant=tenant)
    if request.method == "POST":
        form = InvoiceForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.person = person
            obj.tenant = tenant
            obj.save()
            rows, totals = _invoice_context(person)
            receipts = _receipts_for_person(person)
            resp = render(request, "people/_section_invoices.html", {
                "person": person,
                "invoice_rows": rows,
                "invoice_totals": totals,
                "receipt_list": receipts,
            })
            resp["HX-Trigger"] = json.dumps({"modal_close": True, "billing_changed": True})
            return resp
        return render(request, "people/_form_invoice.html", {"form": form, "person": person})
    form = InvoiceForm()
    return render(request, "people/_form_invoice.html", {"form": form, "person": person})

@login_required
def invoice_edit_partial(request, pk):
    tenant = get_current_tenant(request)
    obj = get_object_or_404(Invoice, pk=pk, tenant=tenant)
    person = obj.person
    if request.method == "POST":
        form = InvoiceForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            rows, totals = _invoice_context(person)
            receipts = _receipts_for_person(person)
            resp = render(request, "people/_section_invoices.html", {
                "person": person,
                "invoice_rows": rows,
                "invoice_totals": totals,
                "receipt_list": receipts,
            })
            resp["HX-Trigger"] = json.dumps({"modal_close": True, "billing_changed": True})
            return resp
        return render(request, "people/_form_invoice.html", {"form": form, "person": person, "invoice": obj})
    form = InvoiceForm(instance=obj)
    return render(request, "people/_form_invoice.html", {"form": form, "person": person, "invoice": obj})

@login_required
def invoice_delete(request, pk):
    inv = get_object_or_404(Invoice, pk=pk)
    person = inv.person
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    inv.delete()
    rows, totals = _invoice_context(person)
    receipts = _receipts_for_person(person)
    return render(request, "people/_section_invoices.html", {
        "person": person,
        "invoice_rows": rows,
        "invoice_totals": totals,
        "receipt_list": receipts,
    })

def _invoice_context(person):
    rows = []
    total_amt = Decimal('0')
    total_paid = Decimal('0')
    for inv in person.invoices.all().prefetch_related('receipts'):
        paid = inv.receipts.aggregate(s=Sum('amount'))['s'] or Decimal('0')
        amt = inv.amount or Decimal('0')
        rows.append({"inv": inv, "paid": paid, "balance": amt - paid})
        total_amt += amt
        total_paid += paid
    totals = {"amount": total_amt, "paid": total_paid, "balance": total_amt - total_paid}
    return rows, totals

@login_required
def invoices_section_partial(request, person_pk):
    tenant = get_current_tenant(request)
    person = get_object_or_404(Person, pk=person_pk, tenant=tenant)
    # reuse your helpers so totals/receipts show up
    invoice_rows, invoice_totals = _invoice_context(person)
    receipt_list = _receipts_for_person(person)
    return render(request, "people/_section_invoices.html", {
        "person": person,
        "invoice_rows": invoice_rows,
        "invoice_totals": invoice_totals,
        "receipt_list": receipt_list,
    })

@login_required
def billing_summary_widget(request, person_pk):
    tenant = get_current_tenant(request)
    person = get_object_or_404(Person, pk=person_pk, tenant=tenant)

    total_amt = person.invoices.aggregate(s=Sum('amount'))['s'] or Decimal('0')
    total_paid = Receipt.objects.filter(invoice__person=person, invoice__tenant=tenant) \
                                .aggregate(s=Sum('amount'))['s'] or Decimal('0')
    balance = total_amt - total_paid

    last_dt = Receipt.objects.filter(invoice__person=person, invoice__tenant=tenant) \
                             .aggregate(m=Max('date'))['m']
    days_since = None
    if last_dt:
        days_since = (timezone.localdate() - last_dt).days

    return render(request, "people/_widget_billing_summary.html", {
        "person": person,
        "balance": balance,
        "days_since": days_since,
    })

# ---- RECEIPTS ----

@login_required
def receipt_new_partial(request, invoice_pk):
    tenant = get_current_tenant(request)
    invoice = get_object_or_404(Invoice, pk=invoice_pk, tenant=tenant)
    person = invoice.person
    if request.method == "POST":
        form = ReceiptForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.invoice = invoice
            obj.tenant = tenant
            obj.save()
            rows, totals = _invoice_context(person)
            receipts = _receipts_for_person(person)
            resp = render(request, "people/_section_invoices.html", {
                "person": person,
                "invoice_rows": rows,
                "invoice_totals": totals,
                "receipt_list": receipts,
            })
            resp["HX-Trigger"] = json.dumps({"modal_close": True, "billing_changed": True})
            return resp
        return render(request, "people/_form_receipt.html", {"form": form, "invoice": invoice, "person": person})
    form = ReceiptForm()
    return render(request, "people/_form_receipt.html", {"form": form, "invoice": invoice, "person": person})


@login_required
def receipt_edit_partial(request, pk):
    tenant = get_current_tenant(request)
    obj = get_object_or_404(Receipt, pk=pk, tenant=tenant)
    person = obj.invoice.person
    if request.method == "POST":
        form = ReceiptForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            rows, totals = _invoice_context(person)
            receipts = _receipts_for_person(person)
            resp = render(request, "people/_section_invoices.html", {
                "person": person,
                "invoice_rows": rows,
                "invoice_totals": totals,
                "receipt_list": receipts,
            })
            resp["HX-Trigger"] = json.dumps({"modal_close": True, "billing_changed": True})
            return resp
        return render(request, "people/_form_receipt.html", {"form": form, "invoice": obj.invoice, "person": person, "receipt": obj})
    form = ReceiptForm(instance=obj)
    return render(request, "people/_form_receipt.html", {"form": form, "invoice": obj.invoice, "person": person, "receipt": obj})

@login_required
def receipt_delete(request, pk):
    rcpt = get_object_or_404(Receipt, pk=pk)
    person = rcpt.invoice.person
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    rcpt.delete()
    rows, totals = _invoice_context(person)
    receipts = _receipts_for_person(person)

    return render(request, "people/_section_invoices.html", {
        "person": person,
        "invoice_rows": rows,
        "invoice_totals": totals,
        "receipt_list": receipts,
    })

def _receipts_for_person(person):
    # all receipts for this person (any invoice), newest first
    return Receipt.objects.select_related('invoice').filter(invoice__person=person).order_by('-date', '-id')

@login_required
def receipt_new_for_person_partial(request, person_pk):
    tenant = get_current_tenant(request)
    person = get_object_or_404(Person, pk=person_pk, tenant=tenant)

    if request.method == "POST":
        form = ReceiptForm(request.POST)
        invoice_id = request.POST.get("invoice")
        invoice = None
        if invoice_id:
            invoice = get_object_or_404(Invoice, pk=invoice_id, tenant=tenant, person=person)

        if form.is_valid() and invoice:
            obj = form.save(commit=False)
            obj.invoice = invoice
            obj.tenant = tenant
            obj.save()
            rows, totals = _invoice_context(person)
            receipts = _receipts_for_person(person)
            resp = render(request, "people/_section_invoices.html", {
                "person": person,
                "invoice_rows": rows,
                "invoice_totals": totals,
                "receipt_list": receipts,
            })
            resp["HX-Trigger"] = json.dumps({"modal_close": True})
            return resp

        if form.is_valid() and not invoice:
            form.add_error(None, "Please choose an invoice.")

        invoices = person.invoices.all().order_by('-date', '-id')
        return render(request, "people/_form_receipt_person.html", {
            "form": form, "person": person, "invoices": invoices
        })

    # GET
    form = ReceiptForm()
    invoices = person.invoices.all().order_by('-date', '-id')
    return render(request, "people/_form_receipt_person.html", {
        "form": form, "person": person, "invoices": invoices
    })

@login_required
def receipt_print(request, pk):
    tenant = get_current_tenant(request)
    receipt = get_object_or_404(
        Receipt.objects.select_related("invoice", "invoice__person"),
        pk=pk, invoice__tenant=tenant
    )
    invoice = receipt.invoice
    person = invoice.person

    invoice_total = invoice.amount or 0
    total_paid_to_date = Receipt.objects.filter(invoice=invoice).aggregate(
        s=Sum("amount")
    )["s"] or 0
    balance_after = max((invoice_total or 0) - (total_paid_to_date or 0), 0)

    return render(request, "people/print_receipt.html", {
        "tenant": tenant,
        "person": person,
        "invoice": invoice,
        "receipt": receipt,
        "invoice_total": invoice_total,
        "total_paid_to_date": total_paid_to_date,
        "balance_after": balance_after,
    })
