"""grocery60_be URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from grocery60_be import views, viewsets, webhook, views_ai
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

router = routers.DefaultRouter()
router.register('cart', viewsets.CartViewset)
router.register('cart-item', viewsets.CartItemViewset)
router.register('catalog', viewsets.CatalogViewset)
router.register('store', viewsets.StoreViewset)
router.register('customer', viewsets.CustomerViewset)
router.register('billing', viewsets.BillingAddressViewset)
router.register('shipping', viewsets.ShippingAddressViewset)
router.register('order', viewsets.OrderViewset)
router.register('order-item', viewsets.OrderItemViewset)
router.register('shipping-method', viewsets.ShippingMethodViewset)
router.register('order-payment', viewsets.OrderPaymentViewset)
router.register('user', viewsets.UserViewset)
router.register('category', viewsets.CategoryViewset)
router.register('storeadmin', viewsets.StoreAdminViewset)
router.register('tax', viewsets.TaxViewset)
router.register('leads', viewsets.LeadsViewset)

handler400 = 'grocery60_be.views.bad_request'
handler401 = 'grocery60_be.views.permission_denied'
handler403 = 'grocery60_be.views.permission_denied'
handler404 = 'grocery60_be.views.not_found'
handler500 = 'grocery60_be.views.server_error'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('customer-payment/', views.CustomerPaymentView.as_view()),
    path('rest-auth/', include('rest_auth.urls')),
    path('order-detail/', views.OrderDetailView.as_view()),
    path('payment/', views.PaymentView.as_view()),
    path('payment/<int:order_id>', views.PaymentView.as_view()),
    path('webhook/payment/', webhook.PaymentWebhookView.as_view()),
    path('rest-auth/login/v1/', views.CustomLoginView.as_view()),
    path('verify/login/', views.VerifyLoginView.as_view()),
    path('forgot/user/', views.ForgotUserView.as_view()),
    path('rest-auth/password/reset/v1/', views.PasswordResetView.as_view()),
    path('rest-auth/password/reset/confirm/v1/', views.PasswordResetConfirmView.as_view()),
    path('email/login/', views.ResendEmailLoginView.as_view()),
    path('stores/login/', views.StoreLoginView.as_view()),
    path('fee/', views.FeeCalView.as_view()),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),

    ### India Views ###
    path('payment/in/', views.IndiaPaymentView.as_view()),
    path('payment/in/<str:razor_order_id>', views.IndiaPaymentView.as_view()),

    ### Product Search AI View ###
    path('productset/', views_ai.ProductSetView.as_view()),
    path('productset/<str:product_set_id>', views_ai.ProductSetView.as_view()),
    path('product/', views_ai.ProductView.as_view()),
    path('product/<int:product_id>', views_ai.ProductView.as_view()),
    path('product/search/', views_ai.ProductSearchView.as_view()),
    path('product/image/search/', views_ai.ProductImageSearchView.as_view()),

]
