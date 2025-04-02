from instabot import Bot
from datetime import datetime
from PIL import Image
import os
import schedule
import time
import math


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


def uploadImage():
    if not os.path.exists(imageFolder):
        os.makedirs(imageFolder)
        print(f"Created {imageFolder} directory")
        return

    todayDate = datetime.now().strftime("%Y-%m-%d")
    caption = f"Song of Today: {todayDate}"

    try:
        imageFiles = [f for f in os.listdir(imageFolder) if f.endswith(('jpg','png','jpeg', 'PNG', 'JPEG', 'JPG'))]
        if not imageFiles:
            print("No images found in the folder")
            return
        
        imageFiles.sort(key=lambda x:os.path.getmtime(os.path.join(imageFolder, x)), reverse=True)
        
        latestImage = None
        for img in imageFiles:
            if not isAlreadyUploaded(img):
                latestImage = os.path.join(imageFolder, img)
                break
        
        if not latestImage:
            print("No new images to upload")
            return

        converted = False
        newImagePath = latestImage
        if not latestImage.lower().endswith('.jpg'):
            try:
                img = Image.open(latestImage)
                base, _ = os.path.splitext(latestImage)
                newImagePath = base + '.jpg'
                img.convert('RGB').save(newImagePath, 'JPEG')
                converted = True
                print(f"Converted image to {newImagePath}")
            except Exception as e:
                print(f"Error converting image: {str(e)}")
                return

        # Process image for Instagram
        processedImage = imageResize(newImagePath)
        if not processedImage:
            print("Failed to process image")
            return
    

        print(f"Uploading {processedImage} with caption: {caption}")
        try:
            cookie_path = "config"
            if os.path.exists(cookie_path):
                import shutil
                shutil.rmtree(cookie_path)

            bot = Bot()
            logged_in = bot.login(
                username=username,
                password=password,
                use_cookie=False,
                is_threaded=True
            )
            
            if not logged_in:
                print("Failed to login to Instagram")
                return
            
            time.sleep(2) 
            
            success = bot.upload_photo(
                processedImage,
                caption=caption
            )
            
            if success:
                logUploadedFile(os.path.basename(latestImage))
                print("Upload successful")
            else:
                print("Upload failed")
                
        except Exception as e:
            print(f"Error during upload: {str(e)}")
        finally:
            if 'bot' in locals() and bot:
                bot.logout()
            if converted and os.path.exists(newImagePath):
                os.remove(newImagePath)
            if processedImage != newImagePath and os.path.exists(processedImage):
                os.remove(processedImage)
    except Exception as e:
        print(f"General error: {str(e)}")

uploadImage()

#schedule.every().day.at("23:00").do(uploadImage)

#while True:
 #   schedule.run_pending()
 #   time.sleep(1)