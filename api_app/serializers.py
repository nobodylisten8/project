from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from api_app.models import Company, Promo, User, PromoComment
from django.core.validators import RegexValidator


class CompanySerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField(max_length=120, min_length=8)
    password = serializers.CharField(min_length=8, max_length=60, validators=[
        RegexValidator(regex=r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
                       message='Incorrect characters')])

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return Company.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.email = validated_data.get('email', instance.email)
        instance.password = validated_data.get('password', instance.password)
        instance.password = make_password(instance.password)
        instance.save()
        return instance


class PromoSerializer(serializers.ModelSerializer):
    target = serializers.JSONField(default=dict)

    class Meta:
        model = Promo
        fields = (
            'description', 'image_url', 'target', 'max_count',
            'active_from', 'active_until', 'mode', 'promo_common',
            'promo_unique', 'active'
        )

    def validate(self, data):
        target = data.get('target', {})
        active_from = target.get('active_from')
        active_until = target.get('active_until')

        if active_from and active_until:
            try:
                active_from = serializers.DateTimeField().to_internal_value(active_from)
                active_until = serializers.DateTimeField().to_internal_value(active_until)
            except serializers.ValidationError:
                raise serializers.ValidationError({
                    "target": "Некорректный формат дат для 'active_from' или 'active_until'."
                })

            if active_from >= active_until:
                raise serializers.ValidationError({
                    "target": "Поле 'active_until' должно быть больше, чем 'active_from'."
                })

        return data

    def create(self, validated_data):
        target = validated_data.get('target', {})
        if 'country' in target and isinstance(target['country'], str):
            target['country'] = target['country'].lower()
        categories = target.get('categories', [])
        if isinstance(categories, list):
            target['categories'] = [str(category).lower() for category in categories if isinstance(category, str)]
        validated_data['target'] = target
        return super().create(validated_data)

    def update(self, instance, validated_data):
        target = validated_data.get('target', instance.target)
        if 'country' in target and isinstance(target['country'], str):
            target['country'] = target['country'].lower()
        instance.target = target
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class UserOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('name', 'surname', 'email', 'avatar_url', 'other')


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    email = serializers.EmailField(max_length=120, min_length=8)
    password = serializers.CharField(min_length=8, max_length=60, validators=[
        RegexValidator(regex=r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
                       message='Incorrect characters')])
    avatar_url = serializers.URLField()
    surname = serializers.CharField()

    other = serializers.JSONField(default=dict)

    class Meta:
        model = User
        fields = (
            "name",
            "surname",
            "email",
            "password",
            "avatar_url",
            "other",
        )

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password:
            instance.password = make_password(password)
        print(validated_data.items())
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class PromoOutSerializer(serializers.ModelSerializer):
    company_id = serializers.UUIDField(source="company.id", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)
    promo_id = serializers.UUIDField(source="id_promo", read_only=True)

    is_activated_by_user = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()

    class Meta:
        model = Promo
        fields = (
            "promo_id",
            "company_id",
            "company_name",
            "description",
            "image_url",
            "active",
            "is_activated_by_user",
            "like_count",
            "is_liked_by_user",
            "comment_count",
        )

    def get_is_activated_by_user(self, obj):
        user = self.context.get("request").user.user
        if user.is_authenticated:
            return str(obj.id_promo) in user.activated_promos
        return False

    def get_is_liked_by_user(self, obj):
        user = self.context.get("request").user.user
        if user.is_authenticated:
            return str(obj.id_promo) in user.liked_promos
        return False

    def get_like_count(self, obj):
        return 0

    def get_comment_count(self, obj):
        return 0


class PromoCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoComment
        fields = '__all__'
        extra_kwargs = {
            'author': {'required': False},
            'promo': {'required': False},
        }

    def create(self, validated_data):
        author = self.context.get('author')
        promo = self.context.get('promo')
        validated_data['author'] = author
        validated_data['promo'] = promo
        return super().create(validated_data)


class UserOutCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('name', 'surname', 'avatar_url')


class PromoCommentOutSerializer(serializers.ModelSerializer):
    author = UserOutCommentSerializer(read_only=True)
    id = serializers.UUIDField(source="comment_id", read_only=True)

    class Meta:
        model = PromoComment
        fields = ('id', 'text', 'date', 'author')


class PromoForCompanyOutSerializer(serializers.ModelSerializer):
    promo_id = serializers.UUIDField(source="id_promo", read_only=True)
    company_id = serializers.UUIDField(source="company.id", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = Promo
        fields = (
            "description",
            "image_url",
            "target",
            'max_count',
            'active_from',
            'active_until',
            'mode',
            'promo_common',
            'promo_unique',
            'promo_id',
            'company_id',
            'company_name',
            "like_count",
            'used_count',
            'active',
        )
