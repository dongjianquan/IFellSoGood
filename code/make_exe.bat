@echo off\


set Installer=D:\ProgramData\Anaconda3\envs\py27\Scripts\pyinstaller.exe


%Installer% -FD cvFilter.py

copy /y .\*.xml .\dependency\
copy /y .\dependency\*.dll .\dist\cvFilter\
copy /y .\dependency\*.xml .\dist\cvFilter\
copy /y .\*.json .\dist\cvFilter\
pause
