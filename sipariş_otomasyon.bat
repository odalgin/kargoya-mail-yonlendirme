@echo off
cd /d "C:\Users\Selvi Masa PC 2\Desktop\coding"
echo [%date% %time%] Script baslatiliyor... >> log.txt
"C:\Users\Selvi Masa PC 2\AppData\Local\Programs\Python\Python313\python.exe" Mail_yonlendirme.py >> log.txt 2>&1
echo [%date% %time%] Script bitti. >> log.txt