import io
import os
import re
import uuid
import mimetypes

import falcon
import msgpack

from PIL import Image
import numpy as np

ALLOWED_IMAGE_TYPES = (
    'image/gif',
    'image/jpeg',
    'image/png',
)

def validate_image_type(req, resp, resource, params):
    if req.content_type not in ALLOWED_IMAGE_TYPES:
        msg = 'Image type not allowed. Must be PNG, JPEG, or GIF'
        raise falcon.HTTPBadRequest('Bad request', msg)

def run_filter(file_loc):
    """Main function"""
    # filename = input("Path to image: ")
    img = Image.open(file_loc).convert('L')

    w = img.size[0]
    h = img.size[1]
    img = shrink(img)

    img = np.asarray(img)
    img.flags.writeable = True
    img = gbc_filter(img)

    img = Image.fromarray(img, 'L')
    img = grow(img,w,h)
    # filename = filename.split(".")[0] + "_gbc_filter.png"
    img.save(file_loc)
    print("Saved to " + file_loc)

def shrink(img):
    width = img.size[0]
    height = img.size[1]

    if width > height:
        w = 128
        h = int((w/width)*height)
        size = w,h
    elif height > width:
        h = 128
        w = int((h/height)*width)
        size = w,h
    elif width == height:
        w = 128
        h = 128
        size = w,h
    return img.resize(size)

def grow(img,width,height):
    size = width,height
    return img.resize(size)

def gbc_filter(img):
    """Applies Game Boy camera filter"""
    for i in range(int(img.shape[0])):
        for j in range(int(img.shape[1])):
            if img[i][j] >= 236:
                img[i][j] = 255
            elif img[i][j] >= 216:
                img[i][j] = 255 - ((i%2)*(j%2)*83)
            elif img[i][j] >= 196:
                img[i][j] = 255 - (((j+i+1)%2)*83)
            elif img[i][j] >= 176:
                img[i][j] = 172 + (((i+1)%2)*(j%2)*83)
            elif img[i][j] >= 157:
                img[i][j] = 172
            elif img[i][j] >= 137:
                img[i][j] = 172 - ((i%2)*(j%2)*86)
            elif img[i][j] >= 117:
                img[i][j] = 172 - (((j+i+1)%2)*86)
            elif img[i][j] >= 97:
                img[i][j] = 86 + (((i+1)%2)*(j%2)*86)
            elif img[i][j] >= 78:
                img[i][j] = 86
            elif img[i][j] >= 58:
                img[i][j] = 86 - ((i%2)*(j%2)*86)
            elif img[i][j] >= 38:
                img[i][j] = 86 - (((j+i+1)%2)*86)
            elif img[i][j] >= 18:
                img[i][j] = 0 + (((i+1)%2)*(j%2)*86)
            else:
                img[i][j] = 0
    return img


class Collection(object):

    def __init__(self, image_store):
        self._image_store = image_store

    def on_get(self, req, resp):
        # TODO: Modify this to return a list of href's based on
        # what images are actually available.
        doc = {
            'images': [
                {
                    'href': '/images/1eaf6ef1-7f2d-4ecc-a8d5-6e8adba7cc0e.png'
                }
            ]
        }

        resp.data = msgpack.packb(doc, use_bin_type=True)
        resp.content_type = falcon.MEDIA_MSGPACK
        resp.status = falcon.HTTP_200

    @falcon.before(validate_image_type)
    def on_post(self, req, resp):
        name = self._image_store.save(req.stream, req.content_type)
        resp.status = falcon.HTTP_201
        resp.location = '/images/' + name


class Item(object):

    def __init__(self, image_store):
        self._image_store = image_store

    def on_get(self, req, resp, name):
        resp.content_type = mimetypes.guess_type(name)[0]

        try:
            resp.stream, resp.stream_len = self._image_store.open(name)
        except IOError:
            raise falcon.HTTPNotFound()


class ImageStore(object):

    _CHUNK_SIZE_BYTES = 4096
    _IMAGE_NAME_PATTERN = re.compile(
        '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.[a-z]{2,4}$'
    )

    def __init__(self, storage_path, uuidgen=uuid.uuid4, fopen=io.open):
        self._storage_path = storage_path
        self._uuidgen = uuidgen
        self._fopen = fopen

    def save(self, image_stream, image_content_type):
        ext = mimetypes.guess_extension(image_content_type)
        name = '{uuid}{ext}'.format(uuid=self._uuidgen(), ext=ext)
        image_path = os.path.join(self._storage_path, name)

        with self._fopen(image_path, 'wb') as image_file:
            while True:
                chunk = image_stream.read(self._CHUNK_SIZE_BYTES)
                if not chunk:
                    break

                image_file.write(chunk)
        
        run_filter(image_path)

        return name

    def open(self, name):
        # Always validate untrusted input!
        if not self._IMAGE_NAME_PATTERN.match(name):
            raise IOError('File not found')

        image_path = os.path.join(self._storage_path, name)
        stream = self._fopen(image_path, 'rb')
        stream_len = os.path.getsize(image_path)

        return stream, stream_len