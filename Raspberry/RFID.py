from tkinter import *
from PIL import Image,ImageTk
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

idTag = 534068541675
idCard = 526049525312
chargerId = 123456
reader = SimpleMFRC522()

win = Tk()
win.geometry("800x480")

try:
    id = reader.read()
        
    if idTag in id or idCard in id:

        #create label
        label = Label(win, font="bold")
        label.pack()
        
        #make a variabel
        x=1

        #Creating pictures
        image = Image.open("autho.png")
        image = image.resize((200,350), Image.ANTIALIAS)
        autho = ImageTk.PhotoImage(image)
        image = Image.open("cable.png")
        image = image.resize((200,350), Image.ANTIALIAS)
        notValid = ImageTk.PhotoImage(image)

        #create a function for moving a picture
        def move():
             global x 

             if x==1:
                 label.config(image=autho)
             elif x==2:
                 label.config(image=notValid)
             x+=1   
             win.after(2000,move)

        move()
        win.mainloop()
        
    else:
        canvas = Canvas(win, width = 200, height = 400)  
        canvas.pack()  
        img = Image.open("notvalid.png")  

        resized_image = img.resize((200,350),Image.ANTIALIAS)
        new_image = ImageTk.PhotoImage(resized_image)

        canvas.create_image(10, 10, anchor=NW, image=new_image) 
        win.mainloop() 
finally:
        GPIO.cleanup()