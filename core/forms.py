
from django import forms
from .models import Person, Indemnitor, Reference, Bond, CourtDate, CheckIn, Invoice, Receipt

class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        exclude = ('tenant',)

class IndemnitorForm(forms.ModelForm):
    class Meta:
        model = Indemnitor
        exclude = ('tenant', 'person')

class ReferenceForm(forms.ModelForm):
    class Meta:
        model = Reference
        exclude = ('tenant', 'person')


class BondForm(forms.ModelForm):
    class Meta:
        model = Bond
        exclude = ('tenant', 'person')

class CourtDateForm(forms.ModelForm):
    class Meta:
        model = CourtDate
        exclude = ('tenant', 'person')

class CheckInForm(forms.ModelForm):
    class Meta:
        model = CheckIn
        exclude = ('tenant', 'person')

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        exclude = ("tenant", "person")

class ReceiptForm(forms.ModelForm):
    class Meta:
        model = Receipt
        exclude = ("tenant", "invoice")