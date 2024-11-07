from PIL import Image

def getbin(image_name):
    im = Image.open(image_name)
    image_width = im.size[0]
    image_height = im.size[1]
    pim = im.load()
    bin_result = ''
    for row in range(image_height):
        for col in range(image_width):
            if pim[col,row][0] == 255:
                bin_result += '1'
            else:
                bin_result += '0'
    return bin_result

bin1 = getbin("C:\\Users\\HW\\Desktop\\kila.png")
print(bin1)