#!/usr/bin/env python
# -*- coding: utf-8 -*-

from fabric.api import sudo, put, run, cd
from fabric.contrib.files import append, exists


def install():
    sudo("apt-get update")
    sudo("apt-get install python-dev python-pip python-opencv libevent-dev python-virtualenv nginx ajaxterm")
    sudo("service apache2 stop")
    sudo("update-rc.d apache2 disable")
    install_adb()


def install_adb():
    put("./adb", "/usr/bin/adb", use_sudo=True)
    sudo("chmod +x /usr/bin/adb")

LOG_PATH = "/var/log/monitor_daemon"


def config(zk):
    def update_hosts(zk):
        append("/etc/hosts", "%s\tzookeeper_server" % zk, use_sudo=True)

    def update_nginx():
        put("./nginx.default", "/etc/nginx/sites-available/default", use_sudo=True)
        sudo("service nginx restart")

    def update_rc_local():
        put("./rc.local", "/etc/rc.local", use_sudo=True)
        sudo("chmod +x /etc/rc.local")

    def update_log_rotate():
        put("./log-rotate", "/etc/logrotate.d/monitor_daemon", use_sudo=True)

    def mkdir_dirs():
        if not exists(LOG_PATH):
            sudo("mkdir %s" % LOG_PATH)
        if not exists("/home/pi/jobs"):
            run("mkdir /home/pi/jobs")

    update_hosts(zk)
    update_nginx()
    update_rc_local()
    mkdir_dirs()
    update_log_rotate()


def deploy(branch="master"):
    if exists("/home/pi/app"):
        with cd("/home/pi/app"):
            run("git checkout -B %s --track origin/%s" % (branch, branch))
            run("git pull")
    else:
        run("git clone -b %s https://github.com/xiaocong/remote-task-http-server.git /home/pi/app" % branch)
    with cd("/home/pi/app"):
        sudo("pip install -r requirements.txt --upgrade")
    restart()


def restart():
    with cd("/home/pi/app"):
        if not exists("/var/run/gunicorn.pid"):
            sudo(
                "gunicorn --access-logfile %s/gunicorn.access.log -u 1000 --pid /var/run/gunicorn.pid -c gunicorn.config.py app:app -D" %
                LOG_PATH, pty=False)
        if exists("/var/run/monitor_daemon.pid"):
            sudo("python monitor_daemon.py stop")
        sudo("python monitor_daemon.py start", pty=False)


def reboot():
    from fabric.api import reboot as rb
    rb()
