import os
import subprocess
import sys
import re
from datetime import datetime

# --- Настройки окружения ---
IMAGE_NAME = "build_tool_image"
PROJECT_DIR = os.getcwd()
REPORTS_DIR = os.path.join(PROJECT_DIR, "reports")

def run_command(command, silent=False):
    if not silent:
        print(f"Exec: {command}")
    
    result = subprocess.run(command, shell=True, capture_output=silent, text=True)
    
    if not silent and result.returncode != 0:
        print(f"Error: {result.stderr}")
        
    return result.returncode == 0, result.stdout if silent else ""

def save_report(mode, success, coverage=None, revision=1):
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{mode}_v{revision}_{timestamp}.txt"
    report_path = os.path.join(REPORTS_DIR, filename)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"=== ОТЧЕТ О СБОРКЕ ===\n")
        f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Ревизия: 1.0.{revision}\n")
        f.write(f"Режим: {mode.upper()}\n")
        f.write(f"Статус: {'УСПЕХ' if success else 'ОШИБКА'}\n")
        
        if coverage is not None:
            f.write(f"Покрытие (Coverage): {coverage}%\n")
            
    print(f"\n[+] Отчет сохранен в: reports/{filename}")

def get_revision_number():
    rev_file = os.path.join(REPORTS_DIR, ".revision")
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)
        
    if os.path.exists(rev_file):
        with open(rev_file, "r") as f:
            rev = int(f.read().strip()) + 1
    else:
        rev = 1
        
    with open(rev_file, "w") as f:
        f.write(str(rev))
    return rev

def build_project(mode, show_logs=False):
    print(f"---- {mode} is in process ----")
    
    revision = get_revision_number()
    base_cmd = "rm -rf build && "
    ccache_flag = "-DCMAKE_C_COMPILER_LAUNCHER=ccache"
    
    # CPack теперь просто запускается, так как вся настройка лежит в нашей Обертке!
    cpack_cmd = "cpack -G DEB"

    if mode == 'release':
        cmd_to_compile = base_cmd + (
            f'cmake -B build -S . -DCMAKE_BUILD_TYPE=Release -DENABLE_CJSON_TEST=Off -DCPACK_PACKAGE_VERSION=1.0.{revision} {ccache_flag} && '
            f'cmake --build build && cd build && {cpack_cmd}'
        )
        
    elif mode == "debug":
        cmd_to_compile = base_cmd + (
            f'cmake -B build -S . -DCMAKE_BUILD_TYPE=Debug -DENABLE_CJSON_TEST=Off -DCPACK_PACKAGE_VERSION=1.0.{revision} {ccache_flag} && '
            f'cmake --build build && cd build && {cpack_cmd}'
        )
        
    elif mode == 'coverage':
        cov_flags = '-DCMAKE_C_FLAGS="--coverage" -DCMAKE_EXE_LINKER_FLAGS="--coverage"'
        cmd_to_compile = base_cmd + (
            f'cmake -B build -S . -DCMAKE_BUILD_TYPE=Debug -DENABLE_CJSON_TEST=On {cov_flags} {ccache_flag} && '
            'cmake --build build && cd build && ctest && '
            'lcov --capture --directory . --output-file coverage.info && '
            'lcov --summary coverage.info'
        )
    else:
        return False

    docker_cmd = f"docker run --rm -v {PROJECT_DIR}:/app {IMAGE_NAME} bash -c '{cmd_to_compile}'"
    success, output = run_command(docker_cmd, silent=not show_logs)
    
    coverage_val = None
    package_generated = (mode in ['release', 'debug'])

    if mode == 'coverage' and success:
        match = re.search(r'lines\.*:\s*(\d+\.\d+)%', output)
        if match:
            coverage_val = float(match.group(1))
            last_cov_file = os.path.join(REPORTS_DIR, ".last_coverage")
            
            if os.path.exists(last_cov_file):
                with open(last_cov_file, "r") as f:
                    last_cov = float(f.read().strip())
                
                if coverage_val < last_cov:
                    print(f"\n[WARNING] Сборка завершается с ошибкой: Покрытие упало с {last_cov}% до {coverage_val}%")
                    success = False
                else:
                    print(f"\n[OK] Покрытие стабильно или выросло: {coverage_val}% (было {last_cov}%). Генерируем артефакт...")
                    package_generated = True
                    run_command(f"docker run --rm -v {PROJECT_DIR}:/app {IMAGE_NAME} bash -c 'cd build && {cpack_cmd}'", silent=True)
            else:
                package_generated = True
                run_command(f"docker run --rm -v {PROJECT_DIR}:/app {IMAGE_NAME} bash -c 'cd build && {cpack_cmd}'", silent=True)
                
            with open(last_cov_file, "w") as f:
                f.write(str(coverage_val))

    save_report(mode, success, coverage_val, revision)
    
    if package_generated and success:
        print(f"[+] Артефакт (deb пакет) версии 1.0.{revision} успешно создан в папке build/")
        
    return success

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 builder.py <release|debug|coverage> [--logs]")
        sys.exit(1)

    print("Checking Docker...")
    image_exists, _ = run_command(f"docker images -q {IMAGE_NAME}", silent=True)
    if not image_exists:
        print("Building Docker image...")
        run_command(f"docker build -t {IMAGE_NAME} .")
    else:
        print("Image already exists.")

    mode_input = sys.argv[1].lower()
    args = sys.argv[2:]
    
    if build_project(mode_input, show_logs=('--logs' in args or '-logs' in args)):
        print(f"\nBuild in {mode_input} mode ended successfully")
    else:
        print("\nFAILED")