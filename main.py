from instabot import Bot
from datetime import datetime
from PIL import Image
from functools import wraps
import os
import schedule
import random
import time
import math
import shutil

def configRemoval():
    path="config"
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
            print("Removed existing config folder.")
        except Exception as e:
            print(f"Error removing config: {str(e)}")

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
uploadLog = "./uploadedFiles.txt"

def isAlreadyUploaded(filename):
    if not os.path.exists(uploadLog):
        return False
    with open(uploadLog, 'r') as f:
        uploadedFiles = f.read().splitlines()
    return filename in uploadedFiles

def logUploadedFile(filename):
    with open(uploadLog, 'a') as f:
        f.write(f"{filename}\n")

def imageResize(imagePath):
    try:
        img = Image.open(imagePath)
        width, height = img.size
        ratio = width / height

        MIN_RATIO = 0.8
        MAX_RATIO = 1.91

        if ratio < MIN_RATIO:
            # Image too tall, adjust height
            new_height = math.floor(width / MIN_RATIO)
            new_width = width
        elif ratio > MAX_RATIO:
            # Image too wide, adjust width
            new_width = math.floor(height * MAX_RATIO)
            new_height = height
        else:
            return imagePath
        
        left = (width - new_width) //2
        top = (height - new_height) //2
        right = left + new_width
        bottom = top + new_height

        imgCropped = img.crop((left, top, right, bottom))
        outputPath = os.path.splitext(imagePath)[0] + '_processed.jpg'
        imgCropped.convert('RGB').save(outputPath, 'JPEG', quality=95)
        return outputPath
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return None

def retryWithBackoff(retries=3, backoffSecs=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            x=0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        raise e
                    sleepTime = (backoffSecs ** 2 ** x + random.uniform(0, 1))
                    time.sleep(sleepTime)
                    x += 1
        return wrapper
    return decorator

@retryWithBackoff(retries=3, backoffSecs=5)
def instagramUpload(bot, photoPath, caption):
    return bot.upload_photo(photoPath, caption=caption)

def uploadImage():
    configRemoval()
    
    if not os.path.exists(imageFolder):
        os.makedirs(imageFolder)
        print(f"Created {imageFolder} directory")
        return

    todayDate = datetime.now().strftime("%Y-%m-%d")
    caption = f"Song of Today: {todayDate}"

    try:
        imageFiles = [f for f in os.listdir(imageFolder) if f.lower().endswith(('jpg','png','jpeg'))]
        if not imageFiles:
            print("No images found in the folder")
            return False

        imageFiles.sort(key=lambda x:os.path.getmtime(os.path.join(imageFolder, x)), reverse=True)
        
        latestImage = next((img for img in imageFiles if not isAlreadyUploaded(img)), None)
        if not latestImage:
            print("No new images to upload")
            return False

        latestImage = os.path.join(imageFolder, latestImage)
        
        converted = False
        newImagePath = latestImage
        processedImage = None
        
        try:
            if not latestImage.lower().endswith('.jpg'):
                img = Image.open(latestImage)
                base, _ = os.path.splitext(latestImage)
                newImagePath = base + '.jpg'
                img.convert('RGB').save(newImagePath, 'JPEG')
                converted = True
                print(f"Converted image to {newImagePath}")

            processedImage = imageResize(newImagePath)
            if not processedImage:
                raise Exception("Failed to process image")

            cookie_path = "config"
            if os.path.exists(cookie_path):
                import shutil
                shutil.rmtree(cookie_path)

            time.sleep(random.uniform(2, 4))  
            
            logged_in = bot.login(
                username=username,
                password=password,
                use_cookie=False,
                is_threaded=True
            )
            
            if not logged_in:
                raise Exception("Failed to login")
            
            time.sleep(random.uniform(3, 5)) 
            
            success = instagramUpload(bot, processedImage, caption)
            
            if success:
                logUploadedFile(os.path.basename(latestImage))
                print("Upload successful")
                return True
            else:
                raise Exception("Upload failed")
                
        except Exception as e:
            print(f"Error during process: {str(e)}")
            return False
        finally:
            if 'bot' in locals() and bot:
                time.sleep(1)
                bot.logout()
            
            for path in [newImagePath, processedImage]:
                if path and path != latestImage and os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception as e:
                        print(f"Error cleaning up {path}: {str(e)}")
                        
    except Exception as e:
        print(f"General error: {str(e)}")
        return False


schedule.every().day.at("23:00").do(uploadImage)

while True:
    schedule.run_pending()
    time.sleep(60)