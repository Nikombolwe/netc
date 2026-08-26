import requests
import json
import logging

# Kuweka Logging kwa ajili ya kufuatilia status za utumaji SMS
logger = logging.getLogger(__name__)

# ==============================================================================
# TAARIFA ZA SDASMS API (Zilizotolewa kutoka attendance/views.py)
# ==============================================================================
SDASMS_API_TOKEN = "165|f2IywyWAhT8qG7TxcGXZKn9cO1jsNq7X4Kg1gcu66db2f0fc"
SDASMS_URL = "https://my.sdasms.com/api/v3/sms/send"
SDASMS_SENDER_ID = "NETC HQ"


def format_phone_number(phone_number):
    """
    Inasafisha na kubadilisha namba ya simu kuwa kwenye format ya Kitanzania (255XXXXXXXXX).
    Mfano: '0712345678' -> '255712345678'
    """
    if not phone_number:
        return None

    # Ondoa nafasi na alama zisizohitajika
    cleaned_number = str(phone_number).strip().replace("+", "").replace(" ", "").replace("-", "")

    # Kama inaanza na '0', ibadilishe kuwa '255'
    if cleaned_number.startswith("0"):
        cleaned_number = "255" + cleaned_number[1:]
    
    # Kama inaanza na '7' au '6' na ina urefu wa tarakimu 9
    elif (cleaned_number.startswith("7") or cleaned_number.startswith("6")) and len(cleaned_number) == 9:
        cleaned_number = "255" + cleaned_number

    return cleaned_number


def send_sms_notification(phone_number, message):
    """
    Function kuu ya kutuma SMS kwa kutumia SDASMS API.
    
    Parameters:
        phone_number (str): Namba ya simu ya mpokeaji.
        message (str): Ujumbe unaotakiwa kutumwa.
        
    Returns:
        bool: True kama SMS imetumwa vizuri, False kama imefeli.
    """
    formatted_phone = format_phone_number(phone_number)

    if not formatted_phone:
        print("[SDASMS Alert]: Namba ya simu haijatolewa au siyo sahihi!")
        logger.error("[SDASMS Error]: Namba ya simu haipo au haina muundo sahihi.")
        return False

    if not message:
        print("[SDASMS Alert]: Ujumbe hauwezi kuwa mtupu!")
        return False

    headers = {
        "Authorization": f"Bearer {SDASMS_API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "recipient": formatted_phone,
        "message": message,
        "sender_id": SDASMS_SENDER_ID
    }

    try:
        # verify=False inazuia SSL certificate error ikiwa ipo
        response = requests.post(
            SDASMS_URL,
            json=payload,
            headers=headers,
            timeout=10,
            verify=False
        )
        
        res_data = response.json()
        print(f"[SDASMS Response to {formatted_phone}]: {res_data}")

        # Kuangalia kama API imerudisha majibu ya mafanikio
        if response.status_code in [200, 201]:
            logger.info(f"[SDASMS Success]: Ujumbe umeenda kwa {formatted_phone}")
            return True
        else:
            logger.error(f"[SDASMS Failed]: Status Code: {response.status_code}, Response: {res_data}")
            return False

    except Exception as e:
        print(f"[SDASMS Error]: Imeshindwa kutuma SMS kwenda {formatted_phone}. Sababu: {str(e)}")
        logger.error(f"[SDASMS Exception]: Hitilafu wakati wa kutuma SMS: {str(e)}")
        return False