from django.http import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from grocery60_be import search_product, settings, models
from google_images_search import GoogleImagesSearch


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
        product = models.Product.objects.get(product_id=product_id)
        gcs_uri = str(product.product_url)
        gcs_uri = gcs_uri.replace('https', 'gs')
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
        image_uri = data.get('image_uri')
        filters = data.get('filters')
        print('Searching set ', product_set_id, ' category ', product_category)
        results = search_product.get_similar_products_file(settings.PROJECT, settings.REGION, product_set_id, product_category,
                                                           image_uri, filters)
        return JsonResponse(results, safe=False)


class ProductImageSearchView(APIView):
    def get(self, request):
        search = request.GET.get('key')
        # you can provide API key and CX using arguments,
        # or you can set environment variables: GCS_DEVELOPER_KEY, GCS_CX
        gis = GoogleImagesSearch(settings.API_KEY, settings.SEARCH_ENGINE_ID)
        # define search params:
        _search_params = {
            'q': search,
            'num': 1
        }

        ## this will only search for images:
        gis.search(search_params=_search_params)


        # search first, then download and resize afterwards:
        gis.search(search_params=_search_params)
        for image in gis.results():
            url = image.url

        return JsonResponse({'image': url}, safe=False)
