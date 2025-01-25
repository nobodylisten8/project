import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone


class BaseEntity(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)

    objects = UserManager()
    USERNAME_FIELD = "id"
    REQUIRED_FIELDS = []

    class Meta:
        abstract = False


class Company(BaseEntity):
    USERNAME_FIELD = 'email'
    email = models.EmailField(unique=True)


class Promo(models.Model):
    company = models.ForeignKey(BaseEntity, on_delete=models.PROTECT)
    id_promo = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField()
    image_url = models.URLField()
    target = models.JSONField(default=dict)
    max_count = models.IntegerField(default=0)
    active_from = models.DateField()
    active_until = models.DateField()
    mode = models.CharField(max_length=20)
    promo_common = models.CharField(max_length=100, blank=True)
    promo_unique = ArrayField(models.CharField(max_length=200), default=list, blank=True)
    active = models.BooleanField(default=True)
    like_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)
    used_count = models.IntegerField(default=0)


class User(BaseEntity):
    USERNAME_FIELD = 'email'
    email = models.EmailField(unique=True)
    surname = models.CharField(max_length=255)
    avatar_url = models.URLField(blank=True, null=True)
    other = models.JSONField(blank=True, null=True)
    activated_promos = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    liked_promos = ArrayField(models.CharField(max_length=100), default=list, blank=True)


class PromoComment(models.Model):
    promo = models.ForeignKey(Promo, on_delete=models.PROTECT)
    date = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    comment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.TextField()
