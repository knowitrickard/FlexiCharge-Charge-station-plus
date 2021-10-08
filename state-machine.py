import PySimpleGUI as sg
import asyncio
import time

from StateHandler import States
from StateHandler import StateHandler
from images import displayStatus

state = StateHandler()

def GUI():
    sg.theme('black')

    startingUpLayout =      [
                                [
                                    sg.Image(data=displayStatus.startingUp(), key='IMAGE', pad = ((0,0),(0,0)), size=(480, 800))  
                                ]       
                            ]

    chargingPercentLayout = [
                                [
                                    sg.Text("0", font=('ITC Avant Garde Std Md', 160), key='PERCENT', text_color='Yellow')
                                ]
                            ]
   
    chargingPercentMarkLayout = [
                                    [
                                        sg.Text("%", font=('ITC Avant Garde Std Md', 55), key='PERCENTMARK', text_color='Yellow')
                                    ]
                                ]

    chargingPowerLayout =   [
                                [  
                                    sg.Text("61 kW at 7.3kWh", font=('Lato', 20), key='POWER', justification='center', text_color='white')
                                ]
                            ]

    chargingTimeLayout =   [
                                [  
                                    sg.Text("4 minutes until full", font=('Lato', 20), key='TIME', justification='center', text_color='white')
                                ]
                            ]
    chargingPriceLayout =   [
                                [  
                                    sg.Text("4.5 SEK per KWH", font=('Lato', 20), key='PRICE', justification='center', text_color='white')
                                ]
                            ]

    background_Window = sg.Window(title="FlexiCharge", layout=startingUpLayout, no_titlebar=True, location=(0,0), size=(480, 800), keep_on_top=False).Finalize()
    background_Window.TKroot["cursor"] = "none"

    chargingPercent_window = sg.Window(title="FlexiChargeChargingPercentWindow", layout=chargingPercentLayout, location=(140, 245), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0,0)).finalize()
    chargingPercent_window.TKroot["cursor"] = "none"
    chargingPercent_window.hide()

    chargingPercentMark_window = sg.Window(title="FlexiChargeChargingPercentWindow", layout=chargingPercentMarkLayout, location=(276, 350), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0,0)).finalize()
    chargingPercentMark_window.TKroot["cursor"] = "none"
    chargingPercentMark_window.hide()

    chargingPower_window = sg.Window(title="FlexiChargeChargingPowerWindow", layout=chargingPowerLayout, location=(162, 645), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0,0)).finalize()
    chargingPower_window.TKroot["cursor"] = "none"
    chargingPower_window.hide()

    chargingTime_window = sg.Window(title="FlexiChargeChargingTimeWindow", layout=chargingTimeLayout, location=(162, 694), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0,0)).finalize()
    chargingTime_window.TKroot["cursor"] = "none"
    chargingTime_window.hide()

    chargingPrice_window = sg.Window(title="FlexiChargeChargingTimeWindow", layout=chargingPriceLayout, location=(125, 525), grab_anywhere=False, no_titlebar=True, background_color='black', margins=(0,0)).finalize()
    chargingPrice_window.TKroot["cursor"] = "none"
    chargingPrice_window.hide()

    return background_Window, chargingPercent_window, chargingPercentMark_window, chargingTime_window, chargingPower_window, chargingPrice_window

window_back, window_chargingPercent, window_chargingPercentMark, window_chargingPower, window_chargingTime, window_chargingPrice = GUI()

#update all the windows
def refreshWindows():
    global window_back, window_chargingPower, window_chargingTime, window_chargingPercent, window_chargingPrice
    window_back.refresh()
    window_chargingPower.refresh()
    window_chargingTime.refresh()
    window_chargingPercent.refresh()
    window_chargingPercentMark.refresh()
    window_chargingPrice.refresh()

async def statemachine():

    global window_back

    #instead of chargerID = 128321 you have to write the follwoing two rows(your ocpp code) to get 
    #the charge id from back-end and display it on screen

    #response = await ocpp_client.send_boot_notification()
    #chargerID = response.charger_id
    chargerID = 128321
    
    firstNumberOfChargerID = int(chargerID % 10) 
    secondNumberOfChargerID = int(chargerID/10) % 10 
    thirdNumberOfChargerID = int(chargerID/100) % 10  
    fouthNumberOfChargerID = int(chargerID/1000) % 10 
    fifthNumberOfChargerID = int(chargerID/10000) % 10 
    sixthNumberOfChargerID = int(chargerID/100000) % 10 
    
    chargerIdLayout =    [
                    [   
                        sg.Text(firstNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID0', justification='center', pad=(20,0)),
                        sg.Text(secondNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID1', justification='center', pad=(25,0)),
                        sg.Text(thirdNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID2', justification='center', pad=(20,0)),
                        sg.Text(fouthNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID3', justification='center', pad=(25,0)),
                        sg.Text(fifthNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID4', justification='center', pad=(20,0)),
                        sg.Text(sixthNumberOfChargerID, font=('Tw Cen MT Condensed Extra Bold', 30), key='ID5', justification='center', pad=(25,0))
                    ]
                ]

    chargerID_window = sg.Window(title="FlexiChargeTopWindow", layout=chargerIdLayout, location=(20,700),keep_on_top=True, grab_anywhere=False, transparent_color=sg.theme_background_color(), no_titlebar=True).finalize()
    chargerID_window.TKroot["cursor"] = "none"
    chargerID_window.hide()

    while True:

        if state.get_state() == States.S_STARTUP:  
            state.set_state(States.S_AVAILABLE)
            time.sleep(1)

        elif state.get_state() == States.S_AVAILABLE:
            #Display QR code image
            window_back['IMAGE'].update(data=displayStatus.qrCode())
            #Show Charger id on screen with QR code image
            chargerID_window.UnHide()
            #update the window
            refreshWindows()   
            #Set the next state to S_PLUGINCABLE
            state.set_state(States.S_PLUGINCABLE)
            #wait 2 sec
            time.sleep(2)

        elif state.get_state() == States.S_PLUGINCABLE:

            window_back['IMAGE'].update(data=displayStatus.plugCable())
            #Hide the charge id on this state
            chargerID_window.Hide()
            refreshWindows()  
            state.set_state(States.S_CONNECTING)
            time.sleep(2)

        elif state.get_state() == States.S_CONNECTING:

            window_back['IMAGE'].update(data=displayStatus.connectingToCar())
            state.set_state(States.S_CHARGING)
            time.sleep(2)

        elif state.get_state() == States.S_CHARGING:

            window_back['IMAGE'].update(data=displayStatus.charging())

            #Display all the windows below during charging image shown on screen
            window_chargingPercent.un_hide()
            window_chargingPercentMark.un_hide()
            window_chargingTime.un_hide()
            window_chargingPower.un_hide()
            window_chargingPrice.un_hide()

            percent = 0
            while True:

                if percent >= 10:
                    #move charging percent on screen when percent >= 10
                    window_chargingPercent.move(60, 245)
                    #move the charging mark (%) on screen
                    window_chargingPercentMark.move(330, 350)                     
                if percent > 10:
                    break

                refreshWindows()
                time.sleep(1)
                percent = percent + 1
                #update in precents how full the battery currently is 
                window_chargingPercent['PERCENT'].update(str(percent))

            state.set_state(States.S_BATTERYFULL)
            time.sleep(2)

        elif state.get_state() == States.S_BATTERYFULL:

            #hide all the windows below during barttery full image shown on screen
            window_chargingPercent.hide()
            window_chargingPercentMark.hide()
            window_chargingTime.hide()
            window_chargingPower.hide()
            window_chargingPrice.hide()

            window_back['IMAGE'].update(data=displayStatus.batteryFull())
            refreshWindows()
            state.set_state(States.S_BATTERYFULL)
            time.sleep(1)

        """ 
        elif state.get_state() == States.S_BATTERYFULL:
            state.set_state(States.S_DISCONNECT)
            window['IMAGE'].update(data=displayStatus.disconnectingFromCar())
            window.refresh()
            time.sleep(2)
             
        else:
            window['IMAGE'].update(data=displayStatus.qrCode())
            window.refresh()
            time.sleep(2) """

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

