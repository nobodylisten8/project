from django.contrib.auth.backends import BaseBackend
from .models import User, Company


class UserAuthBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class CompanyAuthBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            company = Company.objects.get(email=email)
            if company.check_password(password):
                return company
        except Company.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return Company.objects.get(pk=user_id)
        except Company.DoesNotExist:
            return None
