REM This is intended to be run with the .bat file directory as the working dir
if not exist make_tk_exe.bat (
    echo Missing make_tk_exe.bat in working directory
    pause
    exit
)
if not exist text2qti_tk.pyw (
    echo Missing text2qti_tk.pyw in working directory
    pause
    exit
)

REM Create and activate a conda env for packaging the .exe
call conda create -y --name make_text2qti_gui_exe python=3.11 --no-default-packages
call conda activate make_text2qti_gui_exe
REM List conda envs -- useful for debugging
call conda info --envs
REM Install dependencies
pip install bespon
pip install markdown
pip install pyinstaller
if exist ..\setup.py (
    if exist ..\text2qti (
        cd ..
        pip install .
        cd make_gui_exe
    ) else (
        pip install text2qti
    )
) else (
    pip install text2qti
)
REM Build .exe
FOR /F "tokens=* USEBACKQ" %%g IN (`python -c "import text2qti; print(text2qti.__version__)"`) do (SET "TEXT2QTI_VERSION=%%g")
pyinstaller -F --name text2qti_tk_%TEXT2QTI_VERSION% text2qti_tk.pyw
REM Deactivate and delete conda env
call conda deactivate
call conda remove -y --name make_text2qti_gui_exe --all
REM List conda envs -- useful for debugging
call conda info --envs
REM Cleanup
move dist\text2qti_tk_%TEXT2QTI_VERSION%.exe text2qti_tk_%TEXT2QTI_VERSION%.exe
if exist "__pycache__" (
    rd /s /q "__pycache__"
)
rd /s /q "build"
rd /s /q "dist"
del *.spec
pause
