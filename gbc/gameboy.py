from PIL import Image
import numpy as np

def run(file_loc):
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

if __name__ == '__main__':
    run('/home/turing/Pictures/face.jpg')
