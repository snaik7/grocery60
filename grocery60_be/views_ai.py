from django.http import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from grocery60_be import search_product, settings, models


class ProductSetView(APIView):

    def post(self, request):
        data = JSONParser().parse(request)
        product_set = data.get('product_set')
        product_set_display = data.get('product_set_display')
        search_product.create_product_set(settings.PROJECT, settings.REGION, product_set, product_set_display)
        return Response({'msg': 'success'})

    def patch(self, request, product_set_id):
        data = JSONParser().parse(request)
        product_id = data.get('product_id')
        # product_set_id = data.get('product_set_id')
        search_product.add_product_to_product_set(settings.PROJECT, settings.REGION, product_id, product_set_id)
        return Response({'msg': 'success'})


class ProductView(APIView):
    def post(self, request):
        data = JSONParser().parse(request)
        product_id = data.get('product_id')
        product_display_name = data.get('product_display_name')
        product_category = data.get('product_category')
        search_product.create_product(settings.PROJECT, settings.REGION, product_id, product_display_name,
                                      product_category)
        return Response({'msg': 'success'})

    def patch(self, request, product_id):
        data = JSONParser().parse(request)
        product = models.Product.objects.get(id=product_id)
        gcs_uri = str(product.product_url)
        gcs_uri = gcs_uri.replace('https', 'gs')
        gcs_uri = gcs_uri.replace(settings.GS_BUCKET_NAME, settings.GS_BUCKET_NAME+'-ml')
        gcs_uri = gcs_uri.replace('storage.googleapis.com/', '')
        url_split = gcs_uri.split('/')
        reference_image_id = 'I_' + url_split[3]
        search_product.create_reference_image(settings.PROJECT, settings.REGION, str(product_id), reference_image_id,
                                              gcs_uri)
        return Response({'msg': 'success'})


class ProductSearchView(APIView):
    def post(self, request):
        data = JSONParser().parse(request)
        product_set_id = 'PS_'+data.get('store_id')
        product_category = data.get('product_category')
        file_path = data.get('file_path')
        filters = data.get('filters')
        print('Searching set ', product_set_id, ' category ', product_category)
        results = search_product.get_similar_products_file(settings.PROJECT, settings.REGION, product_set_id, product_category,
                                                 file_path, filters)
        return JsonResponse(results, safe=False)
