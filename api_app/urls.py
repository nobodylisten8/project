from django.urls import path
from .views import *

urlpatterns = [
    path('ping', PingView.as_view(), name='ping'),
    path('business/auth/sign-up', RegisterCompanyView.as_view(), name='signup'),
    path('business/auth/sign-in', CompanySinginView.as_view(), name='signin'),
    path('business/promo', PromoListView.as_view(), name='promo-list-create'),
    path('business/promo/<uuid:id_promo>', PromoByIdView.as_view(), name='promo-detail'),
    path('business/promo/<uuid:id_promo>/stat', PromoStatView.as_view(), name='promo-stats'),
    path('user/auth/sign-up', UserRegistrationView.as_view(), name='user-sign-up'),
    path('user/auth/sign-in', UserLoginView.as_view(), name='user-login'),
    path('user/profile', UserProfileView.as_view(), name='profile'),
    path('user/feed', UserFeedView.as_view(), name='user-feed'),
    path('user/promo/<uuid:id_promo>', UserFeedViewById.as_view(), name='user-feed-by-id'),
    path('user/promo/<uuid:id_promo>/like', UserPromoLikeView.as_view(), name='user-promo-like'),
    path('user/promo/<uuid:id_promo>/comments', PromoCommentView.as_view(), name='user-promo-comments'),
    path('user/promo/<uuid:id_promo>/comments/<uuid:comment_id>', PromoCommentViewById.as_view(),
         name='user-promo-comment-by-id'),
    path('user/promo/<uuid:id_promo>/activate', PromoActivateView.as_view(), name='user-promo-activate'),
]
