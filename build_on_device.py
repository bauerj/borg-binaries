#!/bin/env python
import sys
import shutil
import os
import subprocess

BORG_DIR = "/vagrant/borg"
TARGET_DIR = os.path.expanduser("/target/")
PYTHON = "3.6.2"

os.environ["LC_ALL"] = "C"
os.environ["LD_LIBRARY_PATH"] = "/usr/local/lib"

ARCH = "armv6"
_ = subprocess.check_output(["uname", "-m"])
if _.startswith("armv5"):
    ARCH = "armv5"

try:
    os.mkdir(BORG_DIR)
except:
    pass

os.chdir(BORG_DIR)


def install_python(version):
    # Update pyenv
    os.chdir("/root/.pyenv/plugins/python-build/../..")
    subprocess.check_call(["git", "pull"])
    os.chdir(BORG_DIR)
    os.environ['PYTHON_CONFIGURE_OPTS'] = "--enable-shared"
    subprocess.check_call(['pyenv', 'install', '-v', version])


def get_commands_for(vagrantfile):
    with open("/tmp/mod.Vagrantfile.rb", "w") as f:
        with open(vagrantfile) as v:
            for l in v.readlines():
                if "Vagrant.configure" in l:
                    break
                f.write(l + "\n")
        with open("/tmp/run.rb") as r:
            f.write("\n" + r.read())
    # Get only the commands we want
    script = subprocess.check_output(["ruby", "/tmp/mod.Vagrantfile.rb"])
    # Necessary because there is no prebuilt bootloader for WAF
    script = script.replace("python ./waf all", "python ./waf  --no-lsb all")
    # Use newer version of lz4 that was installed from sources
    script = script.replace("liblz4-dev", "")
    return script.splitlines()


def update_git():
    os.chdir(BORG_DIR + "/borg")
    tag = subprocess.check_output(
        ['git', 'describe', '--abbrev=0'])
    os.chdir(BORG_DIR)
    return str(tag.strip())


def clean_build_dir():
    if not os.path.exists("/root/.bash_profile"):
        with open("/root/.bash_profile", "w") as f:
            f.write("")
    for d in ["borg", "pyinstaller"]:
        try:
            shutil.rmtree(BORG_DIR + "/" + d)
        except:
            pass
    subprocess.check_call(["git", "clone", "https://github.com/borgbackup/borg"])
    try:
        os.remove('/vagrant/borg/borg.exe')
    except OSError:
        pass


def build(tag):
    os.chdir(BORG_DIR + "/borg")
    subprocess.check_call(["apt-get", "install", "-y", "ruby"])
    try:
        subprocess.check_call(["apt-get", "remove", "-y", "liblz4-dev", "liblz4-1"])
    except:
        pass
    subprocess.check_call(['git', 'checkout', tag])
    os.environ['LD_LIBRARY_PATH'] = 'root/.pyenv/versions/' + PYTHON + '/lib/'
    _script = get_commands_for("/vagrant/borg/borg/Vagrantfile")
    script = "set -x\n"
    for i in _script:
        script += i + "\n"
    with open("/tmp/vagrantscript", "w") as f:
        f.write(script)
    os.chdir(BORG_DIR)
    subprocess.check_call('sh /tmp/vagrantscript', shell=True)
    shutil.copy2("/vagrant/borg/borg.exe", TARGET_DIR + get_binary_name(tag))


def get_binary_name(tag):
    global ARCH
    return "borg-" + tag + "-" + ARCH


try:
    subprocess.check_call(['pyenv', 'global', PYTHON])
except subprocess.CalledProcessError:
    install_python(PYTHON)
    subprocess.check_call(['pyenv', 'global', PYTHON])

clean_build_dir()
update_git()
if len(sys.argv) < 2:
    tag = update_git()
else:
    tag = sys.argv[1]
print(tag, ARCH)
if os.path.isfile(TARGET_DIR + get_binary_name(tag)):
    print(tag, "already built.")
else:
    build(tag)
