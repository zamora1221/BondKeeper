
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from .models import Tenant
from django.http import HttpResponseForbidden

class TenantAttachMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = None
        if request.user.is_authenticated:
            try:
                request.tenant = request.user.tenant_profile  # OneToOneField related_name='tenant_profile'
            except Tenant.DoesNotExist:
                # either create on the fly or block; pick one:
                # request.tenant = Tenant.objects.create(user=request.user, name=request.user.username)
                return HttpResponseForbidden("No tenant configured for this user.")
        return self.get_response(request)
