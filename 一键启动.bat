start /B "" cmd /c "conda activate youjia && python main.py"
timeout /t 10 >nul
start http://127.0.0.1:7860