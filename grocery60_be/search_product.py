import json

from google.cloud import vision
from grocery60_be import models, settings

from google.cloud import pubsub_v1


def create_product_set_topic(project_id, location, product_set_id, product_set_display_name):
    publisher = pubsub_v1.PublisherClient()
    # The `topic_path` method creates a fully qualified identifier
    # in the form `projects/{project_id}/topics/{topic_id}`
    topic_path = publisher.topic_path(settings.PROJECT, 'productset')

    product_set_dict = {'project_id': project_id, 'location': location, 'product_set_id': product_set_id,
                        'product_set_display_name': product_set_display_name}
    print('product_set_dict', product_set_dict)

    # Data must be a bytestring
    # using encode() + dumps() to convert to bytes
    data_bytes = json.dumps(product_set_dict).encode('utf-8')
    # When you publish a message, the client returns a future.
    future = publisher.publish(topic_path, data=data_bytes)
    print(future.result())


def create_product_set(
        project_id, location, product_set_id, product_set_display_name):
    """Create a product set.
    Args:
        project_id: Id of the project.
        location: A compute region name.
        product_set_id: Id of the product set.
        product_set_display_name: Display name of the product set.
    """
    client = vision.ProductSearchClient()

    # A resource that represents Google Cloud Platform location.
    location_path = client.location_path(
        project=project_id, location=location)

    # Create a product set with the product set specification in the region.
    product_set = vision.types.ProductSet(
        display_name=product_set_display_name)

    # The response is the product set with `name` populated.
    response = client.create_product_set(
        parent=location_path,
        product_set=product_set,
        product_set_id=product_set_id)

    # Display the product set information.
    print('Product set name: {}'.format(response.name))


def create_product_topic(product):
    publisher = pubsub_v1.PublisherClient()
    # The `topic_path` method creates a fully qualified identifier
    # in the form `projects/{project_id}/topics/{topic_id}`
    topic_path = publisher.topic_path(settings.PROJECT, 'product')

    data = {'store_id': str(product.get('store')), 'product_id': str(product.get('product_id')),
            'product_name': product.get('product_name'), 'product_url': product.get('product_url')}
    print('data', data)

    # Data must be a bytestring
    # using encode() + dumps() to convert to bytes
    data_bytes = json.dumps(data).encode('utf-8')
    # When you publish a message, the client returns a future.
    future = publisher.publish(topic_path, data=data_bytes)
    print(future.result())

    print("Published messages.")


def create_product(
        project_id, location, product_id, product_display_name,
        product_category):
    """Create one product.
    Args:
        project_id: Id of the project.
        location: A compute region name.
        product_id: Id of the product.
        product_display_name: Display name of the product.
        product_category: Category of the product.
    """
    client = vision.ProductSearchClient()

    # A resource that represents Google Cloud Platform location.
    location_path = client.location_path(project=project_id, location=location)

    # Create a product with the product specification in the region.
    # Set product display name and product category.
    product = vision.types.Product(
        display_name=product_display_name,
        product_category=product_category)

    # The response is the product with the `name` field populated.
    response = client.create_product(
        parent=location_path,
        product=product,
        product_id=product_id)

    # Display the product information.
    print('Product name: {}'.format(response.name))


def add_product_to_product_set(
        project_id, location, product_id, product_set_id):
    """Add a product to a product set.
    Args:
        project_id: Id of the project.
        location: A compute region name.
        product_id: Id of the product.
        product_set_id: Id of the product set.
    """
    client = vision.ProductSearchClient()

    # Get the full path of the product set.
    product_set_path = client.product_set_path(
        project=project_id, location=location,
        product_set=product_set_id)

    # Get the full path of the product.
    product_path = client.product_path(
        project=project_id, location=location, product=product_id)

    # Add the product to the product set.
    client.add_product_to_product_set(
        name=product_set_path, product=product_path)
    print('Product added to product set.')


def create_reference_image(
        project_id, location, product_id, reference_image_id, gcs_uri):
    """Create a reference image.
    Args:
        project_id: Id of the project.
        location: A compute region name.
        product_id: Id of the product.
        reference_image_id: Id of the reference image.
        gcs_uri: Google Cloud Storage path of the input image.
    """
    client = vision.ProductSearchClient()

    # Get the full path of the product.
    product_path = client.product_path(
        project=project_id, location=location, product=product_id)

    # Create a reference image.
    reference_image = vision.types.ReferenceImage(uri=gcs_uri)

    # The response is the reference image with `name` populated.
    image = client.create_reference_image(
        parent=product_path,
        reference_image=reference_image,
        reference_image_id=reference_image_id)

    # Display the reference image information.
    print('Reference image name: {}'.format(image.name))
    print('Reference image uri: {}'.format(image.uri))


def get_similar_products_file(
        project_id, location, product_set_id, product_category,
        image_uri, filter):
    """Search similar products to image.
    Args:
        project_id: Id of the project.
        location: A compute region name.
        product_set_id: Id of the product set.
        product_category: Category of the product.
        image_uri: URI of the image to be searched.
        filter: Condition to be applied on the labels.
        Example for filter: (color = red OR color = blue) AND style = kids
        It will search on all products with the following labels:
        color:red AND style:kids
        color:blue AND style:kids
    """
    # product_search_client is needed only for its helper methods.
    product_search_client = vision.ProductSearchClient()
    image_annotator_client = vision.ImageAnnotatorClient()

    # Create annotate image request along with product search feature.
    image_source = vision.types.ImageSource(image_uri=image_uri)
    image = vision.types.Image(source=image_source)

    # product search specific parameters
    product_set_path = product_search_client.product_set_path(
        project=project_id, location=location,
        product_set=product_set_id)
    product_search_params = vision.types.ProductSearchParams(
        product_set=product_set_path,
        product_categories=[product_category],
        filter=filter)
    image_context = vision.types.ImageContext(
        product_search_params=product_search_params)

    # Search products similar to the image.
    response = image_annotator_client.product_search(
        image, image_context=image_context)

    index_time = response.product_search_results.index_time
    print('Product set index time:')
    print('  seconds: {}'.format(index_time.seconds))
    print('  nanos: {}\n'.format(index_time.nanos))

    results = response.product_search_results.results

    print('Search results:')
    result_list = []
    for result in results:
        product = result.product
        if result.score > .7:
            print('Score(Confidence): {}'.format(result.score))
            print('Image name: {}'.format(result.image))
            print('result', result)
            print('Product name: {}'.format(product.name))
            print(product.name.split('/'))
            product_id = product.name.split('/')[5]
            _product = models.Product.objects.get(product_id=product_id)
            print('Product display name: {}'.format(
                product.display_name))
            print('Product description: {}\n'.format(product.description))
            print('Product labels: {}\n'.format(product.product_labels))
            image_list = list_reference_images(project_id, location, product_id)
            product_dict = {'score': round(result.score * 100), 'image': result.image, 'product_name': product.name,
                            'display_name': product.display_name, 'description': product.description,
                            'image_url': image_list, 'product_name': _product.product_name, 'product_url':
                                _product.product_url, 'product_category': _product.product_category}

            result_list.append(product_dict)
    return result_list


def list_reference_images(
        project_id, location, product_id):
    """List all images in a product.
    Args:
        project_id: Id of the project.
        location: A compute region name.
        product_id: Id of the product.
    """
    client = vision.ProductSearchClient()

    # Get the full path of the product.
    product_path = client.product_path(
        project=project_id, location=location, product=product_id)

    # List all the reference images available in the product.
    reference_images = client.list_reference_images(parent=product_path)
    image_list = []
    # Display the reference image information.
    for image in reference_images:
        print('Reference image name: {}'.format(image.name))
        print('Reference image id: {}'.format(image.name.split('/')[-1]))
        print('Reference image uri: {}'.format(image.uri))
        print('Reference image bounding polygons: {}'.format(
            image.bounding_polys))
        image_list.append(image.uri.replace('gs://', 'https://storage.cloud.google.com/'))
    return image_list
