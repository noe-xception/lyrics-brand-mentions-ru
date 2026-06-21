

import os
import time
import json
import requests
import pandas as pd
import lyricsgenius
from openai import OpenAI
from typing import Optional, Tuple
from tqdm import tqdm
import numpy as np
import re
import base64
import ast

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)

tqdm.pandas(desc="fetching lyrics")


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
data_path = os.path.join(BASE_DIR, 'data', 'processed', 'dashboard_data', 'df_genres v2.csv')
df_genres = pd.read_csv(data_path)

df_genres['extracted_brands'] = df_genres['extracted_brands'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

exploded_brands = df_genres['extracted_brands'].explode().dropna()

distinct_brands = exploded_brands.str.get('normalized').dropna().unique().tolist()
categories = {
    'cars': [
        'BMW', 'Porsche', 'Cadillac', 'Mercedes-Benz', 'LADA', 'Honda', 
        'Rolls-Royce', 'Land Rover', 'Audi', 'Toyota', 'Brabus', 'Ferrari', 
        'Dodge', 'Lamborghini', 'GAZ', 'Bentley', 'Ducati', 'Infiniti', 
        'Jeep', 'Mini', 'Tesla', 'Suzuki', 'Mazda', 'Peugeot', 'Chevrolet', 
        'McLaren', 'Bugatti', 'Volkswagen'
    ],
    
    'electronics': [
        'Apple', 'Bosch', 'Google', 'Nokia', 'Siemens', 'Nintendo', 
        'LG', 'Microsoft', 'Bluetooth'
    ],
    
    'social media': [
        'Uber', 'Tinder', 'Instagram', 'Badoo', 'WhatsApp', 'PayPal', 
        'Airbnb', 'FaceApp', 'Telegram', 'TikTok', 'YouTube', 'MySpace', 
        'Facebook', 'Odnoklassniki', 'Twitter', 'VK', 'Vinted', 'Yandex', 
        'Spotify', 'Shazam', 'Likee', 'Booking.com', 'Pornhub'
    ],
    
    'luxury clothes': [
        'Hermès', 'Louis Vuitton', 'Stone Island', 'Vans', 'Loro Piana', 
        'Tom Ford', 'Mastermind', 'Tommy Hilfiger', 'Calvin Klein', 'New Rock', 
        'Rick Owens', 'Gucci', 'Nike', 'Adidas', 'Cartier', 'Prada', 'Chanel', 
        'Trapstar', 'Corteiz', 'Under Armour', 'Dolce & Gabbana', "Levi's", 
        'Armani', 'Fendi', 'Tiffany & Co.', 'Brioni', 'Dior', 'Vetements', 
        'Reebok', 'Ralph Lauren', 'DC Shoes', 'Diesel', 'Agent Provocateur', 
        'Ed Hardy', 'Swarovski', 'Martine Rose', 'Polo', 'Miu Miu', 'Mowalola', 
        'Ottolinger', 'Balenciaga', 'Graff', 'Juicy Couture', 'Vlone', 
        'Versace', 'Givenchy', 'Supreme', 'Heron Preston', 'Salvatore Ferragamo', 
        'Maison Margiela', 'Bottega Veneta', 'Jimmy Choo', 'Converse', 
        'OFF-WHITE', 'Burberry', 'Philipp Plein', 'Bulgari', 'Roberto Cavalli', 
        'Ray-Ban', 'Goyard', 'Guess', 'Raf Simons', 'Amiri', 'Bvlgari'
    ],
    
    'weapons': [
        'Mauser', 'Kalashnikov', 'Glock', 'AK-47', 'Ruger', 'MAC-10', 'Cobra'
    ],
    
    'alcohol and smoke': [
        'Macallan', 'Martini', 'Parliament', 'Hennessy', 'Whisky', 
        'Moët & Chandon', 'Kilian', 'Dom Pérignon', 'Chivas Regal', 'Corona', 
        'Johnnie Walker', "Jack Daniel's", 'Bacardi', 'Kent', 'Veuve Clicquot', 
        'Baccarat', 'Philip Morris', 'IQOS', 'Chapman', 'Louis Roederer', 
        'Rothmans', 'Baltika'
    ],
    
    'food': [
        'Mars', 'Sprite', 'Whiskas', 'KFC', "McDonald's", 'Dirol', 
        'Hubba Bubba', 'Skittles', 'Snickers', 'Pulpy', 'Nutella', 
        'Fanta', 'Haribo', 'Foie Gras', 'Nobu', 'Benihana'
    ],
    
    'places': [
        'Yekaterinburg', 'Dubai Mall', 'ЦУМ'
    ],
    
    'persons': [
        'Louis C.K', 'Tupac Shakur', 'Sade', 'Timati', 'Beyoncé', 'Lenny Kravitz', 
        'Vin Diesel', 'Dmitry Nagiev', 'Aarne', 'Rihanna', 'Jeffree Star', 
        'Oxxxymiron', 'Pusha T', 'XXXTentacion', 'Morgenshtern', 'FACE', 
        'Kizaru', 'Feduk', 'Instasamka', 'Arut', 'Lil Pump', 'Smokepurpp', 
        'Pop Smoke', 'Juice WRLD', 'Quentin Tarantino', 'Johnny Dang', 'Eminem', 
        'Dr. Dre', 'G-Unit', 'INSTASAMKA', 'ANIKV', 'SALUKI', 'RAF Camora'
    ],
    
    'other': [
        'Gameloft', 'Zorski', 'Taobao', 'TIMELESS', 'Martini', 'Majestic', 
        'Rolex', 'Vivaldi', 'Rolling Stone', 'RNDM', 'Melon', 'MTV', 'BIC', 
        'Bosco', 'Columbia Pictures', 'Pfizer', 'Lanou', 'Kyivstar', 'UMC', 
        'Advil', 'Cosmopolitan', 'Forbes', 'Fabergé', 'Roche', 'Kaspersky', 
        'IKEA', 'Black Star', 'NBA', 'Кузнецкий мост', 'Villalobos', 'Outline', 
        'Barbie', 'Aeroflot', 'Disney', 'Roblox', 'Peppa Pig', 'Bitcoin', 
        'Novo Nordisk', 'Ubisoft', 'SLAANG', 'Loota', 'Patek Philippe', 'NASA', 
        'Sonic', 'Tracer', 'Namer', 'Spacer', 'Speed Racer', 'Metro', 'Visa', 
        'Mastercard', 'Bugs Bunny', 'GQ', 'Rick and Morty', 'Twister', 'REN TV', 
        'Little Big', 'Coca-Cola', 'Nirvana', 'Adobe', 'LEGO', 'Gazprom', 
        'Virt Squad', 'Netflix', 'Obaku', 'Panamera', 'Audemars Piguet', 'VVS', 
        'Sber', 'Marvel', 'War Thunder', 'Grammy', 'Boeing', 'SpaceX', 'Minecraft', 
        'Queen', 'Willy Wonka', 'Bingo-Bongo', "Rubik's Cube", 'Patrick', 'VIP', 
        'OCB', 'Black Russia', 'Maxim', 'Leica', 'Old Spice', 'Wildberries', 
        'Ozon', 'Lan'
    ]
}

brand_to_group = {brand: group for group, brands in categories.items() for brand in brands}


brand_origins = {
    'LADA': 'Domestic',
    'GAZ': 'Domestic',
    'KamAZ': 'Domestic',
    'Aeroflot': 'Domestic',
    'Gazprom': 'Domestic',
    'Sber': 'Domestic',
    'Kalashnikov': 'Domestic',
    'AK-47': 'Domestic',

    'VK': 'Domestic',
    'Yandex': 'Domestic',
    'Odnoklassniki': 'Domestic',
    'Kaspersky': 'Domestic',
    'Wildberries': 'Domestic',
    'Ozon': 'Domestic',
    'Kyivstar': 'CIS',
    'UMC': 'CIS',

    'Gosha Rubchinskiy': 'Domestic',
    'ЦУМ': 'Domestic',
    'Кузнецкий мост': 'Domestic',
    'Bosco': 'Domestic',
    'Black Star': 'Domestic',
    'SLAANG': 'Domestic',
    'Loota': 'Domestic',

    'REN TV': 'Domestic',
    'Little Big': 'Domestic',
    'Oxxxymiron': 'Domestic',
    'Morgenshtern': 'Domestic',
    'FACE': 'Domestic',
    'Kizaru': 'Domestic',
    'Feduk': 'Domestic',
    'Instasamka': 'Domestic',
    'INSTASAMKA': 'Domestic',
    'Arut': 'Domestic',
    'Timati': 'Domestic',
    'Dmitry Nagiev': 'Domestic',
    'ANIKV': 'Domestic',
    'SALUKI': 'Domestic',
    'RNDM': 'Domestic',
    'Aarne': 'Domestic',

    'Baltika': 'Domestic',
    'Yekaterinburg': 'Domestic',
    'Black Russia': 'Domestic'
}

df_genres['extracted_brands'] = df_genres['extracted_brands'].apply(
    lambda lst: [
        {
            **item, 
            'category': brand_to_group.get(item.get('normalized'), 'other'),
            'origin': brand_origins.get(item.get('normalized'), 'Western/Abroad')
        } 
        for item in lst
    ] if isinstance(lst, list) else []
)

import ast

df_genres['extracted_brands'] = df_genres['extracted_brands'].apply(
    lambda x: ast.literal_eval(x) if isinstance(x, str) else (x if isinstance(x, list) else [])
)

df_genres['extracted_brands'] = df_genres['extracted_brands'].apply(
    lambda lst: list({(item.get('mention'), item.get('normalized')): item for item in lst}.values())
)


df_genres.to_csv(data_path, index=False, encoding='utf-8')





