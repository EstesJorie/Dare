from instabot import Bot
from datetime import datetime
from PIL import Image
import os
import schedule
import time

def loadCredentials(filePath):
    credentials = {}
    try:
        with open(filePath, 'r') as f:
            for line in f:
                if not line.strip() or line.startswith('#'):
                    continue
                key, value = line.strip().split('=')
                credentials[key] = value
    except FileNotFoundError:
        print(f"ERROR: The file {filePath} was not found")
    return credentials

credentials = loadCredentials('login.txt')

username = credentials.get('username')
password = credentials.get('password')

if username and password:
    print(f"Successfully loaded login information for {username}")
else:
    print("ERROR: Could not load login details.")

if username and password:
    bot = Bot()
    bot.login(username=username, password=password)

imageFolder = "./UPLOADS"

def uploadImage():
    todayDate = datetime.now().strftime("%Y-%m-%d")
    caption = f"{todayDate}"

    imageFiles = [f for f in os.listdir(imageFolder) if f.endswith(('jpg','png','jpeg'))]
    if not imageFiles:
        print("No images found in the folder")
        return
    
    imageFiles.sort(key=lambda x:os.path.getmtime(os.path.join(imageFolder, x)), reverse=True)
    latestImage = os.path.join(imageFolder, imageFiles[0])

    if not latestImage.lower().endswith('.jpg'):
        img = Image.open(latestImage)
        newImagePath = os.path.splittext(latestImage[0] + '.jpg')
        img.convert('RGB').save(newImagePath, 'JPEG')
        latestImage = newImagePath
        print(f"Converted image to {latestImage}")

    print(f"Uploading {latestImage} with caption: {caption}")
    bot.upload_photo(latestImage, caption=caption)

schedule.every().day.at("23:00").do(uploadImage)

while True:
    schedule.run_pending()
    time.sleep(1)