import logging
import os
from pathlib import Path
import shutil
import subprocess
import time

import pexpect

DEBIAN_VER = 5
WORK_IMAGE = Path("/tmp/debian-work.qcow2")

BASE_IMAGE = {
    5: Path("debian-lenny.qcow2"),
    6: Path("debian_squeeze_i386_standard.qcow2"),  # https://people.debian.org/~aurel32/qemu/i386/
}[DEBIAN_VER]

logging.basicConfig(level=logging.DEBUG)

# Attempt to detect KVM
if Path("/sys/module/kvm").exists() or Path("/sys/module/kvm_intel").exists():
    kvm_args = ['-enable-kvm']
else:
    kvm_args = []

QEMU_ARGS = kvm_args + [
             '-m', '1024',      # 7-zip needs A LOT of memory
             '-hda', str(WORK_IMAGE),
             '-monitor', 'tcp:127.0.0.1:55555,server,nowait',
             '-nic', 'user,hostfwd=tcp::10022-:22',
             '-nographic',
             ]

SSHPASS = ["sshpass", "-p", "root"]
SSH_OPTIONS = "-q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o Port=10022".split(" ")

logging.debug("Copying base image")
shutil.copyfile(BASE_IMAGE, WORK_IMAGE)

# Based on https://stackoverflow.com/questions/45874326/qemu-guest-automation-using-python-pexpect
logging.debug("Spawning QEMU")
child = pexpect.spawn("qemu-system-i386", QEMU_ARGS)
start = time.time()

# Expected: qemu-system-i386, ssh, sshfs

try:
    if DEBIAN_VER >= 6:
        logging.debug("Awaiting login shell")

        child.expect('login: ', timeout=300)
        logging.info("Got login prompt after %g seconds", time.time() - start)

        # child.sendline('root')
        # time.sleep(1)
        # child.sendline('root')
        # child.expect('# ')
        # logging.debug("Logged in")
    else:
        # The child.expect approach doesn't work for our Debian 5 image, so instead we repeatedly poke the VM over SSH

        ATTEMPT_SECS = 3

        def try_ping():
            try:
                subprocess.check_call([*SSHPASS, "ssh", *SSH_OPTIONS, "root@localhost", "exit"], timeout=ATTEMPT_SECS)
                return True
            except:
                return False

        for i in range(50):
            attempt_start = time.time()

            if try_ping():
                logging.info("VM up after %g seconds", time.time() - start)
                break
            else:
                rem = ATTEMPT_SECS - (time.time() - attempt_start)
                if rem > 0:
                    time.sleep(rem)
        else:
            raise Exception("VM boot timed out")

    logging.debug("Sync files")
    for path in ["phoneME-GP2X-SDL", f"debian-{DEBIAN_VER}/packages", "jars", "tarballs", "build.sh", "test.sh", "termfix.c"]:
        subprocess.check_call([*SSHPASS, "scp", "-r", *SSH_OPTIONS, path, "root@localhost:"])

    logging.debug("Run build script")
    subprocess.check_call([*SSHPASS, "ssh", *SSH_OPTIONS, "root@localhost", "sh build.sh"])

    logging.debug("Exfiltrate results")
    subprocess.check_call([*SSHPASS, "scp", "-r", *SSH_OPTIONS, "root@localhost:build_output.7z", "./"])

    logging.debug("Shutting down")
    subprocess.check_call([*SSHPASS, "ssh", *SSH_OPTIONS, "root@localhost", "poweroff"])
    child.expect(pexpect.EOF)
except BaseException:
    child.close()
    raise


logging.debug("Spawning QEMU")
child = pexpect.spawn("qemu-system-i386", QEMU_ARGS)
start = time.time()

try:
    if DEBIAN_VER >= 6:
        logging.debug("Awaiting login shell")

        child.expect('login: ', timeout=300)
        logging.info("Got login prompt after %g seconds", time.time() - start)
    else:
        # The child.expect approach doesn't work for our Debian 5 image, so instead we repeatedly poke the VM over SSH

        ATTEMPT_SECS = 3

        def try_ping():
            try:
                subprocess.check_call([*SSHPASS, "ssh", *SSH_OPTIONS, "root@localhost", "exit"], timeout=ATTEMPT_SECS)
                return True
            except:
                return False

        for i in range(50):
            attempt_start = time.time()

            if try_ping():
                logging.info("VM up after %g seconds", time.time() - start)
                break
            else:
                rem = ATTEMPT_SECS - (time.time() - attempt_start)
                if rem > 0:
                    time.sleep(rem)
        else:
            raise Exception("VM boot timed out")

    for jar in Path("jars").iterdir():
        logging.debug("Run test script")
        # this will hang in the running midlet. that's ok
        proc = subprocess.Popen([*SSHPASS, "ssh", *SSH_OPTIONS, "root@localhost", f"sh test.sh {jar.name}"])
        time.sleep(30) # TODO: instead of long sleep, bang on the door

        # https://unix.stackexchange.com/questions/426652/connect-to-running-qemu-instance-with-qemu-monitor
        os.system(f"echo screendump {jar.stem}.ppm | nc 127.0.0.1 55555")

        proc.kill()
        time.sleep(3)

        subprocess.check_call(["compare", "-metric", "rmse", f"{jar.stem}.ppm", f"test-expect/{jar.stem}.png", "diff.png"])

    logging.debug("Shutting down")
    subprocess.check_call([*SSHPASS, "ssh", *SSH_OPTIONS, "root@localhost", "poweroff"])
    child.expect(pexpect.EOF)
except BaseException:
    child.close()
    raise
