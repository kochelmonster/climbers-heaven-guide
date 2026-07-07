import os
import time
import pathlib
import http.server
import socketserver
import threading
from compile_guide import transform
import webbrowser


__DIR__ = pathlib.Path(__file__).parent


def update():
    # Your update function logic here
    print("compile...")
    try:
        transform(True)
    except Exception as e:
        print("Error transforming guide", e)
    print("done")


CHECK = True

def monitor_files(directory):
    print(f"Monitoring files in {directory}")
    update()
    file_dict = {}
    while CHECK:
        do_update = False
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                modified_time = os.path.getmtime(file_path)
                # print("file_path", file_path)
                if file_path not in file_dict:
                    file_dict[file_path] = modified_time
                elif file_dict[file_path] != modified_time:
                    print(f"File {file_path} has been modified")
                    file_dict[file_path] = modified_time
                    do_update = True


        if do_update:
            update()
        time.sleep(1)

def main():
    global CHECK

    guide_dir = __DIR__.parent / "docutil"
    monitor_thread = threading.Thread(target=monitor_files, args=(guide_dir,))
    monitor_thread.start()

    html_dir = pathlib.Path(__file__).parents[1] / "output" / "guide" 
    html_dir.mkdir(parents=True, exist_ok=True)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(html_dir), **kwargs)

        def end_headers(self):
            self.send_my_headers()
            http.server.SimpleHTTPRequestHandler.end_headers(self)

        def send_my_headers(self):
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")

        def log_message(self, format, *args):
            return

    for i in range(10):
        server_address = ('', 8090+i)        
        try:
            with socketserver.TCPServer(server_address, Handler) as httpd:
                webbrowser.open_new_tab(f"http://localhost:{server_address[1]}")
                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    print("Shutting down server")
                    CHECK = False
                    monitor_thread.join()
                    return
        except OSError as e:
            print(repr(e))


if __name__ == '__main__':
    main()


