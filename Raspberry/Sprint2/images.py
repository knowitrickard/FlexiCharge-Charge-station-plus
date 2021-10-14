import io
from PIL import Image

def get_img_data(f, maxsize=(480, 800)):
    img = Image.open(f)
    img.thumbnail(maxsize)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    del img
    return bio.getvalue()

class displayStatus:
    def chargeNotAvailable():
        img_chargeNotAvailable = get_img_data('charger_images/Charging.png')
        return img_chargeNotAvailable
    def qrCode():
        img_qrCode = get_img_data('charger_images/QRcode.png')
        return img_qrCode
    def authorizing():
        img_authorizing = get_img_data('charger_images/AuthorizingTag.png')
        return img_authorizing
    def batteryFull():
        img_batteryFull = get_img_data('charger_images/BatteryFull.png')
        return img_batteryFull
    def charging():
        img_charging = get_img_data('charger_images/Charging.png')
        return img_charging
    def chargingCancelled():
        img_chargingCancelled = get_img_data('charger_images/ConnectingToCar.png')
        return img_chargingCancelled
    def disconnectingFromCar():
        img_disconnectingFromCar = get_img_data('charger_images/DisconnectingFromCar.png')
        return img_disconnectingFromCar
    def chargingError():
        img_chargingError = get_img_data('charger_images/errorOccuredWhileCharging.png')
        return img_chargingError
    def flexiChargeApp():
        img_flexiChargeApp = get_img_data('charger_images/FlexiChargeApp.png')
        return img_flexiChargeApp
    def connectingToCar():
        img_connectingToCar = get_img_data('charger_images/ConnectingToCar.png')
        return img_connectingToCar
    def plugCable():
        img_plugCable = get_img_data('charger_images/PlugInTheCable.png')
        return img_plugCable
    def startingUp():
        img_startingUp = get_img_data('charger_images/startingUp.png')
        return img_startingUp
    def tagNotValid():
        img_tagNotValid = get_img_data('charger_images/tagNotValid.png')
        return img_tagNotValid
    def unableToCharge():
        img_unableToCharge = get_img_data('charger_images/unableToCharge.png')
        return img_unableToCharge
    