import os
import sys

def main():
    # Idle worker subprocess modu kontrolü (GUI başlatmadan arka planda çalışır)
    if len(sys.argv) > 1 and sys.argv[1] == "--idle-worker":
        from core.idle_farmer import run_worker
        run_worker(sys.argv[2:])
        sys.exit(0)

    # Achievement worker subprocess modu kontrolü
    if len(sys.argv) > 1 and sys.argv[1] == "--achievement-worker":
        from core.achievement_manager import run_worker
        run_worker(sys.argv[2:])
        sys.exit(0)

    # Sadece Windows ortamındaysak System32 yolunu PATH'e ekle
    if sys.platform == "win32":
        system32 = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32')
        if system32 not in os.environ.get('PATH', ''):
            os.environ['PATH'] = system32 + ';' + os.environ.get('PATH', '')

    from ui_web.bridge import API
    import ui_web.window as web_window

    api = API()
    web_window.run(api)

if __name__ == "__main__":
    main()
