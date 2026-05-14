import os
import sys
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_FILENAME = "reverse_undercover_guardian.py"
TARGET_PATH = os.path.join(SCRIPT_DIR, TARGET_FILENAME)

TOTAL_RUNS = 5
SAVED_COUNT = 0

print(f">>> SAVUNMA TESTİ BAŞLIYOR: Hedef '{TARGET_FILENAME}' ({TOTAL_RUNS} Tur) <<<")
print("-" * 60)

for i in range(1, TOTAL_RUNS + 1):
    print(f"--- RUN #{i} Çalışıyor... ---")
    try:
        result = subprocess.run(
            [sys.executable, TARGET_PATH],
            capture_output=True,
            text=True,
            cwd=SCRIPT_DIR,
        )
        output = result.stdout.upper()
        if result.returncode != 0:
            print(f"⚠️ HATA: Dosya çalışırken çöktü!\n{result.stderr}")
            continue
        if "NO BAN" in output or "INVESTIGATION" in output:
            SAVED_COUNT += 1
            print(f"SONUÇ #{i}: BAŞARILI (Alice Kurtarıldı - Guardian Çalıştı) 🛡️✅")
        elif "BANNED" in output:
            print(f"SONUÇ #{i}: BAŞARISIZ (Alice Banlandı - Guardian Engelleyemedi) ❌")
        else:
            print(f"SONUÇ #{i}: BELİRSİZ ⚠️")
    except FileNotFoundError:
        print(f"🚨 KRİTİK HATA: '{TARGET_PATH}' dosyası bulunamadı!")
        break

protection_rate = (SAVED_COUNT / TOTAL_RUNS) * 100
print("\n" + "=" * 40)
print("🛡️ SAVUNMA GÜCÜ RAPORU")
print("=" * 40)
print(f"Alice'i Kurtarma Oranı: %{protection_rate}")
print("=" * 40)
