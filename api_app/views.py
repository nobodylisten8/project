from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User, Promo, PromoComment
from .serializers import *
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.core.paginator import Paginator, EmptyPage
from .permissions import IsCompany, IsUser
from django.db.utils import IntegrityError


class PingView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response({"status": "PROOOOOOOOOOOOOOOOOOOOD"}, status=status.HTTP_200_OK)


class RegisterCompanyView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            serializer = CompanySerializer(data=request.data)
            if serializer.is_valid():
                new_user = serializer.save()
                refresh = RefreshToken.for_user(new_user)
                return Response({"company_id": new_user.id, 'token': str(refresh)}, status=status.HTTP_200_OK)
        except IntegrityError:
            return Response({"status": "error", "message": "Такой email уже зарегистрирован."},
                            status=status.HTTP_409_CONFLICT)
        return Response({"status": "error", "message": "Ошибка в данных запроса."},
                        status=status.HTTP_400_BAD_REQUEST)


class CompanySinginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            return Response({
                "status": "error",
                "message": "Ошибка в данных запроса."
            }, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, email=email, password=password)
        if user:
            self.invalidate_old_tokens(user=user)
            login(request, user)
            refresh = RefreshToken.for_user(user)
            return JsonResponse({'token': str(refresh)},
                                status=status.HTTP_200_OK)
        return Response({"status": "error", "message": "Неверный email или пароль."},
                        status=status.HTTP_401_UNAUTHORIZED)

    def invalidate_old_tokens(self, user):
        tokens = OutstandingToken.objects.filter(user=user)
        for token in tokens:
            if not BlacklistedToken.objects.filter(token=token).exists():
                BlacklistedToken.objects.create(token=token)


class PromoListView(APIView):
    permission_classes = (IsAuthenticated, IsCompany,)

    def post(self, request):
        serializer = PromoSerializer(data=self.request.data)
        if serializer.is_valid():
            new_promo = serializer.save(company=self.request.user)
            return Response({'id': new_promo.id_promo}, status=status.HTTP_201_CREATED)
        return Response({"status": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        queryset = Promo.objects.filter(company_id=self.request.user.id)
        countries = request.query_params.getlist('country', [])
        if countries:
            queryset = queryset.filter(target__country__in=[country.lower() for country in countries])

        sort_by = request.query_params.get('sort_by')
        if sort_by in ['active_from', 'active_until']:
            queryset = queryset.order_by(sort_by)

        limit = int(request.query_params.get('limit', 10))
        offset = int(request.query_params.get('offset', 0))
        paginator = Paginator(queryset, limit)
        total_count = paginator.count
        try:
            promos = paginator.page((offset // limit) + 1)
        except EmptyPage:
            return Response({
                "status": "error",
                "message": "No data available for the requested page."
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer = PromoForCompanyOutSerializer(promos, many=True)
        response = Response(serializer.data, status=status.HTTP_200_OK)
        response['X-Total-Count'] = total_count

        return response


class PromoByIdView(APIView):
    permission_classes = (IsAuthenticated, IsCompany)

    def get(self, request, id_promo):
        try:
            promo = Promo.objects.get(id_promo=id_promo, company_id=request.user.id)
        except Promo.DoesNotExist:
            return Response({"status": "error", "message": "Promo does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = PromoForCompanyOutSerializer(promo)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, id_promo):
        try:
            promo = Promo.objects.get(id_promo=id_promo, company_id=request.user.id)
        except Promo.DoesNotExist:
            return Response({"error": "Promo not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PromoSerializer(promo, data=request.data, partial=True)
        if serializer.is_valid():
            updated_promo = serializer.save()
            return Response(PromoForCompanyOutSerializer(updated_promo).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PromoStatView(APIView):
    permission_classes = (IsAuthenticated, IsCompany,)

    def get(self, request, id_promo):
        try:
            promo = Promo.objects.get(id_promo=id_promo)
            serializer = PromoSerializer(promo)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Promo.DoesNotExist:
            return Response({"error": "Promo not found."}, status=status.HTTP_404_NOT_FOUND)


class UserRegistrationView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        new_user = UserSerializer(data=request.data)

        if new_user.is_valid():
            saved_user = new_user.save()
            refresh = RefreshToken.for_user(saved_user)
            return Response({"token": str(refresh)}, status=status.HTTP_201_CREATED)
        return Response({"status": "bad"}, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, email=email, password=password)
        if user:
            self.invalidate_old_tokens(user)
            login(request, user)
            refresh = RefreshToken.for_user(user)
            return JsonResponse({'token': str(refresh)},
                                status=status.HTTP_200_OK)
        return Response({"status": "bad"}, status=status.HTTP_400_BAD_REQUEST)

    def invalidate_old_tokens(self, user):
        tokens = OutstandingToken.objects.filter(user=user)
        for token in tokens:
            if not BlacklistedToken.objects.filter(token=token).exists():
                BlacklistedToken.objects.create(token=token)


class UserProfileView(APIView):
    permission_classes = (IsAuthenticated, IsUser,)

    def get(self, request):
        UserProfile = User.objects.filter(id=request.user.id)
        if UserProfile.exists():
            return Response({'profile': UserOutSerializer(UserProfile, many=True).data})
        return Response({"status": "bad"}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        UserProfile = User.objects.get(id=request.user.id)
        serializer = UserSerializer(instance=UserProfile, data=request.data, partial=True)
        if serializer.is_valid():
            updated_user = serializer.save()
            return Response(UserOutSerializer(updated_user).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserFeedView(APIView):
    permission_classes = (IsAuthenticated, IsUser,)

    def get(self, request):
        queryset = Promo.objects.all()
        category = request.query_params.get('category', "")
        limit = int(request.query_params.get('limit', 10))
        offset = int(request.query_params.get('offset', 0))
        active = request.query_params.getlist('active', True)

        if category:
            queryset = queryset.filter(target__categories__contains=[category.strip().lower()])

        if active:
            queryset = queryset.filter(active=True)

        paginator = Paginator(queryset, limit)
        total_count = paginator.count
        try:
            promos = paginator.page((offset // limit) + 1)
        except EmptyPage:
            return Response({
                "status": "error",
                "message": "No data available for the requested page."
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer = PromoOutSerializer(promos, many=True, context={"request": request})
        response = Response({
            "status": "success",
            "count": paginator.count,
            "data": serializer.data
        }, status=status.HTTP_200_OK)
        response['X-Total-Count'] = total_count

        return response


class UserFeedViewById(APIView):
    permission_classes = (IsAuthenticated, IsUser,)

    def get(self, request, id_promo):
        try:
            promo = Promo.objects.get(id_promo=id_promo)
        except Promo.DoesNotExist:
            return Response({"status": "error", "message": "Promo does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = PromoOutSerializer(promo, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserPromoLikeView(APIView):
    permission_classes = (IsAuthenticated, IsUser,)

    def post(self, request, id_promo):
        promo = get_object_or_404(Promo, id_promo=id_promo)
        user = request.user.user
        if str(id_promo) in user.liked_promos:
            return Response(status=status.HTTP_200_OK, data={"status": "ok"})
        user.liked_promos.append(id_promo)
        user.save()
        promo.like_count += 1
        promo.save()
        return Response({"status": "success"}, status=status.HTTP_200_OK)

    def delete(self, request, id_promo):
        promo = get_object_or_404(Promo, id_promo=id_promo)
        user = request.user.user
        if str(id_promo) in user.liked_promos:
            user.liked_promos.remove(str(id_promo))
            user.save()
            promo.like_count -= 1
            promo.save()
            return Response(status=status.HTTP_200_OK, data={"status": "ok"})
        else:
            return Response(status=status.HTTP_200_OK, data={"status": "error"})


class PromoCommentView(APIView):
    permission_classes = (IsAuthenticated, IsUser,)

    def post(self, request, id_promo):
        promo = get_object_or_404(Promo, id_promo=id_promo)
        author = request.user.user
        serializer = PromoCommentSerializer(data=request.data, context={"author": author, "promo": promo})
        if serializer.is_valid():
            new_comment = serializer.save()
            return Response(PromoCommentOutSerializer(new_comment).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, id_promo):
        queryset = PromoComment.objects.filter(promo__id_promo=id_promo)
        queryset = queryset.order_by('-date')
        limit = int(request.query_params.get('limit', 10))
        offset = int(request.query_params.get('offset', 0))

        paginator = Paginator(queryset, limit)
        total_count = paginator.count
        try:
            promos = paginator.page((offset // limit) + 1)
        except EmptyPage:
            return Response({
                "status": "error",
                "message": "No data available for the requested page."
            }, status=status.HTTP_400_BAD_REQUEST)
        serializer = PromoCommentOutSerializer(promos, many=True)
        response = Response(serializer.data, status=status.HTTP_200_OK)
        response['X-Total-Count'] = total_count

        return response


class PromoCommentViewById(APIView):
    permission_classes = (IsAuthenticated, IsUser,)

    def get(self, request, id_promo, comment_id):
        current_promo_comment = PromoComment.objects.get(promo__id_promo=id_promo, comment_id=comment_id)
        serializer = PromoCommentOutSerializer(current_promo_comment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id_promo, comment_id):
        current_promo_comment = PromoComment.objects.get(promo__id_promo=id_promo, comment_id=comment_id)
        if current_promo_comment:
            serializer = PromoCommentOutSerializer(current_promo_comment, data=request.data)
            if serializer.is_valid():
                updated_promo_comment = serializer.save()
                return Response(PromoCommentOutSerializer(updated_promo_comment).data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id_promo, comment_id):
        current_promo_comment = PromoComment.objects.get(promo__id_promo=id_promo, comment_id=comment_id)
        current_promo_comment.delete()
        return Response(data={"status": "ok"}, status=status.HTTP_200_OK)


class PromoActivateView(APIView):
    permission_classes = (IsAuthenticated, IsUser,)

    def post(self, request, id_promo):
        try:
            promo = get_object_or_404(Promo, id_promo=id_promo)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_404_NOT_FOUND)
        if not promo.active:
            return Response(status=status.HTTP_403_FORBIDDEN)
        user = get_object_or_404(User, id=request.user.id)
        if not (promo.target.get('age_from') <= user.other.get('age') <= promo.target.get('age_until')):
            return Response(status=status.HTTP_403_FORBIDDEN)
        if user.other.get('country') != promo.target.get('country'):
            return Response(status=status.HTTP_403_FORBIDDEN)
        # todo antifraud
        if promo.mode.upper() == "COMMON" and promo.max_count <= 0:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if promo.mode.upper() == "UNIQUE" and len(promo.promo_unique) == 0:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if promo.mode.upper() == "UNIQUE":
            code = promo.promo_unique.pop(0)
            promo.save()
            return Response(data={"code": code}, status=status.HTTP_200_OK)
        if promo.mode.upper() == "COMMON":
            code = promo.promo_common
            promo.max_count -= 1
            promo.save()
            return Response(data={"code": code}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
