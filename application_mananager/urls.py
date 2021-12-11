"""
    coding=utf-8
"""
from django.urls import path
from .views import ProductListAPIView, ProductDetailAPIView, UploadClients, create_file, clients_manager, \
    clients_detail, bills_manager, bills_detail, bills_product_manager, bills_product_detail

urlpatterns = [
    path('product/list/', ProductListAPIView.as_view(), name="listproducts"),
    path('product/detailed/<int:pk>/', ProductDetailAPIView.as_view(), name="listproducts"),
    path('product/update/<int:pk>/', ProductDetailAPIView.as_view(), name="updateproducts"),
    path('product/delete/<int:pk>/', ProductDetailAPIView.as_view(), name="deleteproducts"),
    path('product/create/', ProductListAPIView.as_view(), name="createproduct"),

    path('client/upload/', UploadClients.as_view(), name="uploadclient"),
    path('client/download/', create_file, name="downloadfile"),
    path('client/list/', clients_manager, name="listclient"),
    path('client/create/', clients_manager, name="createclient"),
    path('client/detailed/<int:pk>/', clients_detail, name="createclient"),
    path('client/update/<int:pk>/', clients_detail, name="updateclient"),
    path('client/delete/<int:pk>/', clients_detail, name="deleteclient"),

    path('bill/list/', bills_manager, name="listclient"),
    path('bill/create/', bills_manager, name="createclient"),
    path('bill/detailed/<int:pk>/', bills_detail, name="createclient"),
    path('bill/update/<int:pk>/', bills_detail, name="updateclient"),
    path('bill/delete/<int:pk>/', bills_detail, name="deleteclient"),

    path('bill_product/list/', bills_product_manager, name="listclient"),
    path('bill_product/create/', bills_product_manager, name="createclient"),
    path('bill_product/detailed/<int:pk>/', bills_product_detail, name="createclient"),
    path('bill_product/delete/<int:pk>/', bills_product_detail, name="deleteclient"),
]
