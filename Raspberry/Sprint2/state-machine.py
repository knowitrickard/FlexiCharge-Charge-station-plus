import asyncio
from tkinter import font
import websockets
import json
import time
import multiprocessing
import io
import PySimpleGUI as sg
import platform
import time
from StateHandler import States
from StateHandler import StateHandler

from PIL import Image, ImageTk
from multiprocessing import Process

from images import displayStatus

state = StateHandler()
lastState = StateHandler()


def GUI():
    sg.theme('Black')

    layout1 =    [
                    [
                        sg.Text(" ")
                    ],
                    [
                        sg.Image(data=displayStatus.startingUp(), key='IMAGE', size=(480, 800))
                        
                    ]
                ]

    window = sg.Window(title="FlexiCharge", layout=layout1, no_titlebar=True, location=(0,0), size=(480,800), keep_on_top=False).Finalize()
    window.TKroot["cursor"] = "none"
    screen = 0

    return window


async def statemachine():
    window = GUI()
    global state
    global lastState
     
    while True:

        if state.get_state() == States.S_STARTUP:
            time.sleep(2)  
            state.set_state(States.S_AVAILABLE)
            window['IMAGE'].update(data=displayStatus.qrCode())
            window.refresh()
            sg.Text(" hhhhhhhhhhhhhhh ")
            time.sleep(2)
            
       
        elif state.get_state() == States.S_AVAILABLE:    
            state.set_state(States.S_AUTHORIZING)
            window['IMAGE'].update(data=displayStatus.authorizing())
            window.refresh()
            time.sleep(2)
        
        elif state.get_state() == States.S_AUTHORIZING:
            state.set_state(States.S_PLUGINCABLE)
            window['IMAGE'].update(data=displayStatus.plugCable())
            window.refresh()
            time.sleep(2)
        
        elif state.get_state() == States.S_PLUGINCABLE:
            state.set_state(States.S_CONNECTING)
            window['IMAGE'].update(data=displayStatus.connectingToCar())
            window.refresh()
            time.sleep(2)
        
        elif state.get_state() == States.S_CONNECTING:
            state.set_state(States.S_CHARGING)
            window['IMAGE'].update(data=displayStatus.charging())
            window.refresh()
            time.sleep(2)
        
        elif state.get_state() == States.S_CHARGING:
            state.set_state(States.S_BATTERYFULL)
            window['IMAGE'].update(data=displayStatus.batteryFull())
            window.refresh()
            time.sleep(2)
        
        elif state.get_state() == States.S_BATTERYFULL:
            state.set_state(States.S_DISCONNECT)
            window['IMAGE'].update(data=displayStatus.disconnectingFromCar())
            window.refresh()
            time.sleep(2)
             
        else:
            window['IMAGE'].update(data=displayStatus.qrCode())
            window.refresh()
            time.sleep(2)

"""def RFID():
    reader = SimpleMFRC522()
    try:
        id = reader.read()    
        if idTag in id or idCard in id:
            print("Tag ID:", id)
        else
            print(id, "Not Valid")
    finally:
        GPIO.cleanup()"""
       

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(statemachine())
