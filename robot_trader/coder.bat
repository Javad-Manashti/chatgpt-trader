@echo off
tree /f > codes.txt
for /r %%i in (*.py) do (
    echo --------------------------------------------------- >> codes.txt
    echo %%i >> codes.txt
    echo. >> codes.txt
    type %%i >> codes.txt
    echo. >> codes.txt
)
