import threading
import spur
import shutil
import sys
import subprocess
import time
import os

DIR = os.path.dirname(os.path.realpath(__file__))


class Qemu:
    def __init__(self, arch):
        self.arch = arch
        self.popen = None

    def start(self):
        try:
            self.popen = subprocess.Popen(["systemd", "start", "qemu-{}".format(self.arch)], shell=True)
            print("Starting QEMU VM...")
        except:
            pass

    def stop(self):
        self.popen = subprocess.Popen(["systemd", "stop", "qemu-{}".format(self.arch)], shell=True)


servers = [
    ("localhost", 10023, Qemu("armhf"), "helicarrier"),
    ("localhost", 10022, Qemu("arm"), "quinjet")
]


class logger:
    _minlen = 1

    def __init__(self, name):
        self.name = name
        if len(name) > logger._minlen:
            logger._minlen = len(name)
        self.logf = open(name + ".log", "w")
        self.buffer = ""
        self.lock = threading.Lock()

    def log(self, s):
        self.write(s + "\n")

    def minlen(self, s, _len):
        while len(s) < _len:
            s = " " + s + " "
        if len(s) > _len:
            s = s[1:]
        return s

    def ts(self):
        return time.strftime("%H:%M:%S", time.gmtime())

    def write(self, s):
        with self.lock:
            if "\n" not in s:
                self.buffer += s
                return
            for l in s.split("\n"):
                if not len(l) and not len(self.buffer):
                    continue
                print(self.ts(), "[" + self.minlen(self.name, logger._minlen) + "]:", self.buffer + l)
                self.logf.write(self.buffer + l + "\n")
                self.buffer = ""


def start_build(server, cargs):
    l = logger(server[3])
    script_file = "/tmp/build_on_device.py"
    if len(server) > 2 and server[2]:
        server[2].start()
    l.log("Starting build")
    shell = spur.SshShell(hostname=server[0],
                          username="root",
                          private_key_file="arm_build_rsa",
                          port=server[1],
                          missing_host_key=spur.ssh.MissingHostKey.accept)
    while True:
        try:
            with shell.open(script_file, "wb") as destination:
                l.log("Connected")
                with open("build_on_device.py", "r") as source:
                    shutil.copyfileobj(source, destination)
                break
        except:
            l.log("Connection is not ready")
            time.sleep(2)
    with shell.open("/tmp/run.rb", "wb") as destination:
        with open("run.rb", "r") as source:
            shutil.copyfileobj(source, destination)
    l.log("Files copied")
    shell.run(["python2", script_file] + cargs, stdout=l, stderr=l)
    res = shell.run(["ls", "/target/"])
    for file in res.output.split():
        targetfile = "/var/www/borg_binaries/" + file
        if os.path.isfile(targetfile): continue
        with shell.open("/target/" + file, "rb") as source:
            with open(targetfile, "wb") as destination:
                shutil.copyfileobj(source, destination)
                l.log("Downloaded " + file)
    if len(server) > 2 and server[2]:
        server[2].stop()


cargs = sys.argv[1:]
threads = []
for s in servers:
    t = threading.Thread(target=start_build, args=(s, cargs))
    t.start()
    threads.append(t)
    time.sleep(10)
for t in threads:
    t.join()
