from rest_framework.permissions import BasePermission
from .models import Company, User


class IsCompany(BasePermission):

    def has_permission(self, request, view):
        return bool(request.user and Company.objects.filter(id=request.user.id).exists())


class IsUser(BasePermission):

    def has_permission(self, request, view):
        return bool(request.user and User.objects.filter(id=request.user.id).exists())
