import os
import sys
import subprocess
from pathlib import Path

def setup_app_environment(app_dir, app_name):
    """
    Настраивает окружение для запуска приложения
    Возвращает модифицированную команду для запуска
    """
    app_path = Path(app_dir)
    
    if sys.platform == "win32":
        # Для Windows приложений
        if app_name.lower() == "musm":
            # Ищем mpv.dll в директории приложения и подпапках
            dll_found = False
            dll_paths = []
            
            # Проверяем основную директорию
            for dll_name in ["mpv-1.dll", "mpv-2.dll", "libmpv-2.dll", "mpv.dll"]:
                dll_path = app_path / dll_name
                if dll_path.exists():
                    dll_found = True
                    dll_paths.append(str(dll_path.parent))
                    break
            
            # Ищем в подпапках
            if not dll_found:
                for root, dirs, files in os.walk(app_path):
                    for file in files:
                        if file.lower() in ["mpv-1.dll", "mpv-2.dll", "libmpv-2.dll", "mpv.dll"]:
                            dll_paths.append(root)
                            dll_found = True
            
            if dll_found:
                # Добавляем все найденные пути в PATH
                for dll_dir in dll_paths:
                    if dll_dir not in os.environ["PATH"]:
                        os.environ["PATH"] = dll_dir + os.pathsep + os.environ["PATH"]
                
                # Создаем bat файл для запуска с правильным окружением
                bat_content = f"""@echo off
chcp 65001 >nul
title {app_name} - Launcher

REM Добавляем пути к DLL в PATH
set "ORIGINAL_PATH=%PATH%"
"""
                for dll_dir in dll_paths:
                    bat_content += f'set "PATH={dll_dir};%PATH%"\n'
                
                bat_content += f"""
echo Starting {app_name} with DLL support...
cd /d "{app_dir}"
python main.py
set "PATH=%ORIGINAL_PATH%"
pause
"""
                
                bat_path = app_path / f"run_{app_name}.bat"
                with open(bat_path, "w", encoding="utf-8") as f:
                    f.write(bat_content)
                
                return str(bat_path)
    
    return None

def create_wrapper_script(app_dir, app_name, original_script):
    """
    Создает обертку для запуска Python скриптов с настройкой окружения
    """
    app_path = Path(app_dir)
    
    if sys.platform == "win32":
        # Создаем bat файл для Windows
        wrapper_content = f"""@echo off
chcp 65001 >nul
title {app_name} - Wrapper

REM Сохраняем оригинальный PATH
set "ORIGINAL_PATH=%PATH%"

REM Добавляем директорию приложения в PATH
set "PATH={app_dir};%PATH%"

REM Ищем DLL файлы в подпапках
for /r "{app_dir}" %%i in (mpv-1.dll mpv-2.dll libmpv-2.dll mpv.dll) do (
    set "DLL_DIR=%%~dpi"
    if not "!DLL_DIR!"=="!DLL_DIR:%%PATH%%=!" (
        set "PATH=!DLL_DIR!;!PATH!"
    )
)

echo Starting {app_name}...
cd /d "{app_dir}"
python "{original_script}"

REM Восстанавливаем оригинальный PATH
set "PATH=%ORIGINAL_PATH%"
pause
"""
        
        wrapper_path = app_path / f"wrapper_{app_name}.bat"
        with open(wrapper_path, "w", encoding="utf-8") as f:
            f.write(wrapper_content)
        
        return str(wrapper_path)
    
    elif sys.platform == "darwin":
        # Для macOS
        wrapper_content = f"""#!/bin/bash
cd "{app_dir}"
export DYLD_LIBRARY_PATH="{app_dir}:$DYLD_LIBRARY_PATH"
python3 "{original_script}"
"""
        
        wrapper_path = app_path / f"wrapper_{app_name}.command"
        with open(wrapper_path, "w", encoding="utf-8") as f:
            f.write(wrapper_content)
        
        os.chmod(wrapper_path, 0o755)
        return str(wrapper_path)
    
    else:  # Linux
        wrapper_content = f"""#!/bin/bash
cd "{app_dir}"
export LD_LIBRARY_PATH="{app_dir}:$LD_LIBRARY_PATH"
python3 "{original_script}"
"""
        
        wrapper_path = app_path / f"wrapper_{app_name}.sh"
        with open(wrapper_path, "w", encoding="utf-8") as f:
            f.write(wrapper_content)
        
        os.chmod(wrapper_path, 0o755)
        return str(wrapper_path)

def run_with_dll_support(app_dir, app_name, main_script="main.py"):
    """
    Запускает приложение с поддержкой DLL
    """
    wrapper_script = create_wrapper_script(app_dir, app_name, main_script)
    
    if wrapper_script and os.path.exists(wrapper_script):
        if sys.platform == "win32":
            subprocess.Popen(['start', 'cmd', '/k', wrapper_script], shell=True)
        elif sys.platform == "darwin":
            subprocess.Popen(['open', '-a', 'Terminal', wrapper_script])
        else:
            subprocess.Popen(['x-terminal-emulator', '-e', wrapper_script])
        return True
    
    return False

def find_and_setup_dll(app_dir):
    """
    Находит DLL файлы и настраивает окружение
    """
    app_path = Path(app_dir)
    dll_dirs = set()
    
    # Ищем все DLL файлы
    for root, dirs, files in os.walk(app_path):
        for file in files:
            if file.lower().endswith('.dll'):
                dll_dirs.add(root)
                break
    
    # Добавляем найденные директории в PATH
    if dll_dirs:
        for dll_dir in dll_dirs:
            if str(dll_dir) not in os.environ["PATH"]:
                os.environ["PATH"] = str(dll_dir) + os.pathsep + os.environ["PATH"]
        
        return True
    
    return False