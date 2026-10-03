import json
import logging
import requests

logger = logging.getLogger(__name__)

# ==============================================================================
# TAARIFA ZA SDASMS API
# ==============================================================================
SDASMS_API_TOKEN = (
    "1b0b6c399f46bff4798ea3e6883df2586891b78c23e69a4efd4e7682c434134f"
)
SDASMS_URL = "https://www.swahilisms.co.tz/api/v1/sms/send"
SDASMS_SENDER_ID = "NETC HQ"  # Imebadilishwa kulingana na Default Sender ID ya akaunti yako [cite: 1]


def format_phone_number(phone_number):
  if not phone_number:
    return None

  cleaned_number = (
      str(phone_number)
      .strip()
      .replace("+", "")
      .replace(" ", "")
      .replace("-", "")
  )

  if cleaned_number.startswith("0") and len(cleaned_number) == 10:
    cleaned_number = "255" + cleaned_number[1:]
  elif (cleaned_number.startswith("7") or cleaned_number.startswith("6")) and len(
      cleaned_number
  ) == 9:
    cleaned_number = "255" + cleaned_number

  if cleaned_number.startswith("255") and len(cleaned_number) == 12:
    return cleaned_number

  return None


def send_sms_notification(phone_number, message):
  formatted_phone = format_phone_number(phone_number)

  if not formatted_phone:
    print(
        f"[SDASMS Alert]: Namba ya simu '{phone_number}' siyo sahihi au ina"
        " upungufu wa tarakimu!"
    )
    logger.error(f"[SDASMS Error]: Namba batili imekataliwa: {phone_number}")
    return False

  if not message:
    print("[SDASMS Alert]: Ujumbe hauwezi kuwa mtupu!")
    return False

  # Ondoa Authorization Bearer, weka Content-Type pekee
  headers = {"Content-Type": "application/json", "Accept": "application/json"}

  #api_token imeingizwa ndani ya payload kama inavyooneshwa kwenye doc [cite: 1]
  payload = {
      "api_token": SDASMS_API_TOKEN,
      "recipient": formatted_phone,
      "message": message,
      "sender_id": SDASMS_SENDER_ID,
  }

  try:
    response = requests.post(
        SDASMS_URL, json=payload, headers=headers, timeout=15, verify=False
    )

    try:
      res_data = response.json()
    except json.JSONDecodeError:
      res_data = response.text

    print(
        f"[SDASMS Response to {formatted_phone}]: Status"
        f" {response.status_code} - {res_data}"
    )

    if response.status_code in [200, 201]:
      logger.info(f"[SDASMS Success]: Ujumbe umeenda kwa {formatted_phone}")
      return True
    else:
      logger.error(
          f"[SDASMS Failed]: Status Code: {response.status_code}, Response:"
          f" {res_data}"
      )
      return False

  except Exception as e:
    print(
        "[SDASMS Error]: Imeshindwa kutuma SMS kwenda"
        f" {formatted_phone}. Sababu: {str(e)}"
    )
    logger.error(
        f"[SDASMS Exception]: Hitilafu wakati wa kutuma SMS: {str(e)}"
    )
    return False