@echo off
echo === FamilyGuard Backend ===
echo Installation des dependances...
pip install -r requirements.txt
echo.
echo Demarrage du serveur sur http://0.0.0.0:8000
echo Tableau de bord accessible sur http://localhost:8000
echo.
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
