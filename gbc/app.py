import os

import falcon

from .images import ImageStore, Collection, Item

def create_app(image_store):
    api = falcon.API()
    api.add_route('/images', Collection(image_store))
    api.add_route('/images/{name}', Item(image_store))
    return api


def get_app():
    storage_path = os.environ.get('LOOK_STORAGE_PATH', '.')
    image_store = ImageStore(storage_path)
    return create_app(image_store)
