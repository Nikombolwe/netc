import requests
import sys

# URL ya API ya Attendance
URL = "http://127.0.0.1:8000/attendance/api/scan/"

def print_banner():
    print("=" * 45)
    print("   FINGERPRINT SCANNER SIMULATOR (NETC)   ")
    print("=" * 45)
    print("Andika 'q' au bonyeza Ctrl+C kutoka.\n")

def main():
    print_banner()
    
    while True:
        try:
            code = input("Ingiza Code / Fingerprint ID: ").strip()
            
            if code.lower() == 'q':
                print("\nSimulator imefungwa. Siku njema!")
                break
                
            if not code:
                print("⚠️ Tafadhali ingiza code iliyo sahihi.\n")
                continue

            # Kutuma data kwenda Django API
            payload = {'employee_code': code}
            response = requests.post(URL, data=payload, timeout=5)
            
            try:
                result = response.json()
            except ValueError:
                print(f"\n❌ Server imerudisha jibu lisiloeleweka (Status Code: {response.status_code})")
                print("---------------------------------------------\n")
                continue

            # Kuonyesha matokeo kulingana na status
            print("\n" + "-" * 40)
            status = result.get('status', 'error').upper()
            
            if status == 'SUCCESS':
                action = result.get('action')
                user = result.get('employee', 'Mtumiaji')
                time = result.get('time')
                
                print(f"✅ STATUS  : MAFANIKIO ({action})")
                print(f"👤 MHUSIKA : {user}")
                print(f"⏰ MUDA    : {time}")
            
            elif status == 'WARNING':
                print(f"⚠️ STATUS  : TAHADHARI")
                print(f"💬 UJUMBE  : {result.get('message')}")
                
            else:
                print(f"❌ STATUS  : KOSA ({response.status_code})")
                print(f"💬 UJUMBE  : {result.get('message', 'Kosa lisilojulikana')}")
                
            print("-" * 40 + "\n")

        except KeyboardInterrupt:
            print("\n\nSimulator imefungwa.")
            sys.exit(0)
            
        except requests.exceptions.ConnectionError:
            print("\n❌ SHIDA YA MTANDAO: Hakikisha Django Server inarun (`python manage.py runserver`)\n")
            
        except requests.exceptions.Timeout:
            print("\n❌ TIMEOUT: Server imechukua muda mrefu kujibu.\n")

if __name__ == "__main__":
    main()