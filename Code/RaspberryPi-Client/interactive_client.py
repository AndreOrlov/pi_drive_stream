import socket
import sys
import platform

def getch():
    """Читает один символ без ожидания Enter (кроссплатформенно)"""
    if platform.system() == 'Windows':
        # Windows
        import msvcrt
        return msvcrt.getch().decode('utf-8')
    else:
        # Unix/Linux/Mac
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

HOST = '192.168.1.54'  # Замените на IP Raspberry Pi
PORT = 5051

commands = {
    '1': 'DirForward',
    '2': 'DirBack',
    '3': 'DirLeft',
    '4': 'DirRight',
    '5': 'DirStop',
    'w': 'CamUp',
    's': 'CamDown',
    'a': 'CamLeft',
    'd': 'CamRight'
}

print("Подключение к Raspberry Pi...")
print("Команды:")
print("  1 - Вперед")
print("  2 - Назад")
print("  3 - Влево")
print("  4 - Вправо")
print("  5 - Стоп")
print("  w - Камера вверх")
print("  s - Камера вниз")
print("  a - Камера влево")
print("  d - Камера вправо")
print("  q - Выход")

try:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    print(f"Подключено к {HOST}:{PORT}")

    print("\nГотов к приему команд (нажмите клавишу)...")

    while True:
        cmd = getch().lower()

        if cmd == 'q':
            print("\nВыход...")
            break

        if cmd in commands:
            client.send(commands[cmd].encode())
            print(f"\r{commands[cmd]:<20}", end='', flush=True)
        else:
            print(f"\r? Неизвестная команда [{cmd}]", end='', flush=True)

    client.close()
except Exception as e:
    print(f"Ошибка: {e}")
