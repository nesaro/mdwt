"""print calendar entries stored with calcurse"""
import subprocess
import cog

def print_calcurse():
    cog.outl(subprocess.run(["calcurse", "-d", "10", "--format-apt", " * %S -> %E %m\n", "--format-recur-apt", " * %S -> %E %m\n"],
                            capture_output=True).stdout.decode())


