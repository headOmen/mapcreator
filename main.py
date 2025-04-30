import argparse
import os
import math
from tkinter import *
from posix import getlogin
from tkinter.ttk import Combobox
from super_image import EdsrModel, ImageLoader

from PIL import Image
import folium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

parser = argparse.ArgumentParser(description="main.py")
parser.add_argument('-lat', type=float, help='Latitude', default=54.778245)
parser.add_argument('-long', type=float, help='Longitude', default=32.051993)
args = parser.parse_args()

center_lat = args.lat
center_long = args.long
radius = [41000, 21000, 11000, 7000] # meters
tile_size = 256 #px
earthCircumference = 40075016.686;
images = []

def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 1 << zoom
    xtile = (lon_deg + 180.0) / 360.0 * n
    ytile = (1.0 - math.log(math.tan(lat_rad) + (1.0 / math.cos(lat_rad))) / math.pi) / 2.0 * n
    return (xtile, ytile)

def creating_paths(zoom, xtile, ytile):
        login = getlogin()
        default_path = '/home/' + login + "/.tiles/" + str(zoom) + "/"
        images.append(default_path + "%d/%d.png" % (xtile, ytile))
        print(xtile, ytile)

def marge_tiles(w, h, r):
    if r == 7000:
        return
    main_image = Image.new('RGB', (w * tile_size, h * tile_size), (255, 255, 255))
    for i in range(w):
        for j in range(h):
            image = Image.open(images[i * h + j])
            main_image.paste(image, (tile_size * i, tile_size * j))
    main_image.save('raw7km.png', 'PNG')
    main_image.save('raw' + str(int(r / 1000)) + 'km.png', 'PNG')
    images.clear()

def crop_image(im, r, crop):
    crop_value = 0
    if r == 7000:
        crop_value = crop#640
    elif r == 11000:
        crop_value = crop#996
    elif r == 21000:
        crop_value = crop#980
    elif r == 41000:
        crop_value = crop#930
    cropped = im.crop(((im.width - crop_value) // 2,
             (im.height - crop_value) // 2,
             (im.width + crop_value) // 2,
             (im.height + crop_value) // 2))
    return cropped


def create_map():
    cur_lat = float(lat_entry.get())
    for r in radius:
        zoom = 0
        if r == 7000:
            zoom = 12
        elif r == 11000:
            zoom = 11
        elif r == 21000:
            zoom = 10
        elif r == 41000:
            zoom = 9
        pixelWidth = tile_size * math.pow(2, zoom)
        meterWidth = earthCircumference * math.cos(cur_lat * math.pi / 180.0)
        pixelsPerMeter = pixelWidth / meterWidth
        px_km = int(pixelsPerMeter * r * 2)
        print(r, px_km)
        if enabled.get() == 0:
            xt, yt = deg2num(float(lat_entry.get()), float(lon_entry.get()), zoom)
            xshift = (xt - int(xt)) * tile_size
            yshift = (yt - int(yt)) * tile_size
            for x in range(int(xt) - 3, int(xt) + 4):
                for y in range(int(yt) - 3, int(yt) + 4):
                    creating_paths(zoom, x, y)
            marge_tiles(7,7, r)
            img = Image.open('raw' + str(int(r / 1000)) + 'km.png')
            img = img.crop((xshift, yshift, img.width - (tile_size - xshift), img.height - (tile_size - yshift)))
            img = crop_image(img, r, px_km)
            img.save('map' + str(int(r / 1000)) + 'km.png')
            os.remove(os.getcwd() + '/raw' + str(int(r / 1000)) + 'km.png')
        else:
            options = Options()
            options.add_argument('--headless')
            driver = webdriver.Chrome(options=options)
            driver.set_window_size(1920, 1080)
            if combobox.get() == "Схема":
                os_map = folium.Map(location=[float(lat_entry.get()), float(lon_entry.get())], zoom_start=zoom)
            elif combobox.get() == "Спутник":
                os_map = folium.Map(location=[float(lat_entry.get()), float(lon_entry.get())],
                                    zoom_start=zoom,
                                    tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', attr='Google')
            elif combobox.get() == "Гибрид":
                os_map = folium.Map(location=[float(lat_entry.get()), float(lon_entry.get())],
                            zoom_start=zoom,
                            tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google')

            os_map.save(str(r) + '.html')
            html_url = 'file://{0}/{1}'.format(os.getcwd(), str(r) + '.html')
            driver.get(html_url)
            time.sleep(2)
            driver.save_screenshot('raw' + str(int(r / 1000)) + 'km.png')
            crop_image(Image.open('raw' + str(int(r / 1000)) + 'km.png'), r, px_km).save('map' + str(int(r / 1000)) + 'km.png')
            os.remove(os.getcwd() + "/" + str(r) + '.html')
            os.remove(os.getcwd() + '/raw' + str(int(r / 1000)) + 'km.png')
            driver.quit()
            # upscale image
            if upscale.get():
                image = Image.open('map' + str(int(r / 1000)) + 'km.png')
                model = EdsrModel.from_pretrained('eugenesiow/edsr-base', scale=2)
                inputs = ImageLoader.load_image(image)
                preds = model(inputs)
                ImageLoader.save_image(preds, 'map' + str(int(r / 1000)) + 'km.png')

main = Tk()
main.title("Создать карты")
lat_lbl = Label(main, text="Широта: ")
lon_lbl = Label(main, text="Долгота: ")
lat_entry = Entry(main, bg="white", fg="black", width=20)
lon_entry = Entry(main, bg="white", fg="black", width=20)
enabled = IntVar()
upscale = IntVar()
chk_button_eth = Checkbutton(main, text="Из интернета?", variable=enabled)
chh_button_upscale = Checkbutton(main, text="Апскейлить?", variable=upscale)
map_variable = ["Схема", "Спутник", "Гибрид"]
combobox = Combobox(main, value=map_variable)
btn = Button(main, bg="white", fg="black", width=20, height=1, command=create_map, text="Создать карты")
lat_lbl.grid(row=0, column=0)
lon_lbl.grid(row=1, column=0)
lat_entry.grid(row=0, column=1)
lon_entry.grid(row=1, column=1)
combobox.grid(row=2, column=0)
chk_button_eth.grid(row=2, column=1)
chh_button_upscale.grid(row=3, column=1)
btn.grid(row=3, column=0)
main.mainloop()












