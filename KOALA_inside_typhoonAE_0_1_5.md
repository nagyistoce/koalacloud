KOALA can run inside a Private Cloud PaaS with [typhoonAE](http://code.google.com/p/typhoonae/).

This tutorial shows how to start typhoonAE inside Ubuntu 9.04 (Jaunty Jackalope) and run KOALA inside typhoonAE.

# What typhoonAE is #

typhoonAE runs inside [Xen](http://www.xen.org) or VMware instances and inside [Amazon EC2](http://aws.amazon.com/ec2/) instances too. The software consists of the App Engine SDK, some open source components to provide the App Engine functionalities and some Python scripts. Almost all services of Google’s App Engine are implemented, except incoming mail. The typhoonAE [Road Map](http://code.google.com/p/typhoonae/wiki/RoadMap) has more information about this.

# Installation of typhoonAE and KOALA #

At first you neet do install a few packages

```
# apt-get install gcc g++ make python-imaging python2.5 python2.5-dev subversion
# apt-get install libmysql++-dev libncurses5-dev  libssl-dev  gettext  erlang-nox erlang-dev 
# apt-get install libexpat1-dev
```

The next steps should be done as user and not root!

The next steps are described in detail at typhoonAE's [Getting Started](http://code.google.com/p/typhoonae/wiki/GettingStarted) page.

Get typhoonAE

```
$ wget http://typhoonae.googlecode.com/files/typhoonae-buildout-0.1.5.tar.gz
$ tar -xvzf typhoonae-buildout-0.1.5.tar.gz 
$ cd typhoonae-buildout-0.1.5
```

Check your Python version

```
$ python2.5 --version
Python 2.5.4
```

Build the stack

```
$ python2.5 bootstrap.py
$ ./bin/buildout
```

Get the KOALA code and run it inside typhoonAE

```
$ svn checkout http://koalacloud.googlecode.com/svn/trunk/ koalacloud
$ cd typhoonae-buildout-0.1.5/
$ ./bin/apptool /home/bauni/koalacloud/
$ ./bin/supervisord
```

Check if all typhoonAE services are up and running

```
#./bin/supervisorctl
ejabberd                         RUNNING    pid 32625, uptime 0:59:20
intid                            RUNNING    pid 32691, uptime 0:59:20
koalacloud:koalacloud_00         RUNNING    pid 434, uptime 0:54:02
koalacloud:koalacloud_01         RUNNING    pid 433, uptime 0:54:02
koalacloud:koalacloud_02         RUNNING    pid 436, uptime 0:54:02
koalacloud:koalacloud_03         RUNNING    pid 435, uptime 0:54:02
koalacloud_deferred_taskworker   RUNNING    pid 32685, uptime 0:59:20
koalacloud_taskworker            RUNNING    pid 32647, uptime 0:59:20
memcached                        RUNNING    pid 32630, uptime 0:59:20
mongod                           RUNNING    pid 32623, uptime 0:59:20
nginx                            RUNNING    pid 32697, uptime 0:59:20
rabbitmq                         RUNNING    pid 32624, uptime 0:59:20
```

Now, you can reach KOALA at [http://localhost:8080](http://localhost:8080)

# It works #

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/KOALA_in_typhoonAE_1_29_8_2010_small.jpg](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/KOALA_in_typhoonAE_1_29_8_2010_small.jpg)

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/KOALA_in_typhoonAE_2_29_8_2010_small.jpg](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/KOALA_in_typhoonAE_2_29_8_2010_small.jpg)

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/KOALA_in_typhoonAE_3_29_8_2010_small.jpg](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/KOALA_in_typhoonAE_3_29_8_2010_small.jpg)

# Some helpful commands #

Shutdown typhoonAE with

```
./bin/supervisorctl shutdown
```

If you want to run more appservers with KOALA, change the value of **numprocs** inside **/etc/koalacloud-supervisor.conf** in the section **fcgi-program:koalacloud**. If you change this variable e.g. to the value 4, the supervisord of typhoonAE starts 4 appservers for KOALA.

If you changed the applications settings in **/etc/koalacloud-supervisor.conf** you can tell typhoonAE this

```
./bin/supervisorctl update
```

The supervisor web interface run at [http://localhost:9001](http://localhost:9001)

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/KOALA_in_typhoonAE_4_29_8_2010_small.jpg](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/KOALA_in_typhoonAE_4_29_8_2010_small.jpg)