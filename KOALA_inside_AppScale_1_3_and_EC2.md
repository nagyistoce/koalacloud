[KOALA](http://koalacloud.appspot.com) can run inside a Private Cloud PaaS with [AppScale](http://appscale.cs.ucsb.edu).

This tutorial shows how to start AppScale 1.3 inside EC2 and upload KOALA into the AppScale PaaS.

# What AppScale is #

AppScale is a platform that allows users to deploy and host their own Google App Engine applications. AppScale executes automatically over [Amazon EC2](http://aws.amazon.com/ec2/) and [Eucalyptus](http://open.eucalyptus.com) as well as [Xen](http://www.xen.org) and [KVM](http://www.linux-kvm.org) and supports both the Python and Java Google App Engine platforms.

# Installation of AppScale and KOALA #

At first you neet do install the [appscale-tools](http://code.google.com/p/appscale/).

Pack the KOALA sourcecode into a tar.gz

```
$ cd koalacloud
$ tar -cvzf koalacloud.tar.gz . --exclude=tutorial
$ mv koalacloud.tar.gz ../
```

Start AppScale PaaS inside EC2 (this needs some time).

```
$ appscale-run-instances --file ~/workspace/koalacloud.tar.gz --table voldemort
--max 2 --machine ami-14799b7d --keyname appscaletest -v

... lots of output here ...

Head node successfully created at ec2-204-236-248-30.compute-1.amazonaws.com. It is now starting up voldemort via the command line arguments given.
Killing and starting server at ec2-204-236-248-30.compute-1.amazonaws.com
Please wait for the controller to finish pre-processing tasks.

This AppScale instance is linked to an e-mail address giving it administrator privileges.
Enter your desired administrator e-mail address: baun@kit.edu
Please repeat your e-mail address to verify: baun@kit.edu

The new administrator password must be at least six characters long and can include non-alphanumeric characters.
Enter your new password: ***secret***
Enter again to verify: ***secret***
Please wait for AppScale to prepare your machines for use.
Spawning up 1 virtual machines
Copying over needed files and starting the AppController on the other VMs
Starting up Voldemort on the head node
Done starting up AppScale, now in heartbeat mode
Run instances: UserAppServer is at ec2-204-236-248-30.compute-1.amazonaws.com

Your user account has been created successfully.
Uploading koalacloud...
We have reserved the name koalacloud for your application.
koalacloud was uploaded successfully.
Please wait for your app to start up.

Your app can be reached at the following URL: http://ec2-204-236-248-30.compute-1.amazonaws.com/apps/koalacloud
The status of your AppScale instance is at the following URL: http://ec2-204-236-248-30.compute-1.amazonaws.com/status
```

There is a known bug inside the AppScale image that causes the web server not to start. The image tries to start the web server too soon before the load balancers configuration (/etc/nginx/sites-enabled/load-balancer.conf) is available. Therefore, you need to log in into the instance and restart the nginx web server manually.

```
$ ssh -i ~/.appscale/appscaletest.private ec2-204-236-248-30.compute-1.amazonaws.com -l root
# invoke-rc.d nginx restart
Restarting nginx: nginx.
```

This is the status page of AppScale where you can see the AppScale instances.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale_1_started_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale_1_started_small.png)

When you switch to KOALA, you need to log first.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale_2_KOALA_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale_2_KOALA_small.png)

**Login** redirects you to the AppScale login page.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale_3_login_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale_3_login_small.png)

After your successful login, you can switch back to KOALA.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale_4_login_successful_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale_4_login_successful_small.png)

KOALA is ready for work now. At least you need to import your credentials which is described [here](http://code.google.com/p/koalacloud/wiki/First_Steps_with_EC2_and_KOALA).

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale_5_start_working_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale_5_start_working_small.png)

When your AWS credentials are imported, you can manage the instances with KOALA that run KOALA and the AppScale PaaS

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale_6_aws_inside_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale_6_aws_inside_small.png)

This are the two AppScale instances inside EC2 that contain KOALA itself.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale_7_redundant_view_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale_7_redundant_view_small.png)

You can check the AppScale instances also with the command appscale-describe-instances.

```
$ appscale-describe-instances --keyname appscaletest
Status of node at ec2-204-236-248-30.compute-1.amazonaws.com:
    Currently using 2.1 Percent CPU and 12.43 Percent Memory
    Database is at ec2-204-236-248-30.compute-1.amazonaws.com
    Hosting the following apps: koalacloud
    Current State: Done starting up AppScale, now in heartbeat mode
Status of node at ec2-184-72-173-167.compute-1.amazonaws.com:
    Currently using 1.4 Percent CPU and 14.37 Percent Memory
    Database is at ec2-184-72-173-167.compute-1.amazonaws.com
    Hosting the following apps: koalacloud
    Current State: Preparing to run AppEngine apps if needed
```

To terminate the AppScale instances, you can use the command appscale-terminate-instances.

```
$ appscale-terminate-instances --keyname appscaletest
About to terminate instances spawned via ec2 with keyname 'appscaletest'...
INSTANCE	i-1d473077	running	shutting-down
INSTANCE	i-19423573	running	shutting-down
Terminated AppScale across 2 boxes.
```

Alternatively you can use KOALA. :-)

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale_8_terminate_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale_8_terminate_small.png)