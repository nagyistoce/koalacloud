[KOALA](http://koalacloud.appspot.com) can run inside a Private Cloud PaaS with [AppScale](http://appscale.cs.ucsb.edu).

This tutorial shows how to start AppScale 1.4 inside EC2 and upload KOALA into the AppScale PaaS.

# What [AppScale](http://appscale.cs.ucsb.edu) is #

[AppScale](http://appscale.cs.ucsb.edu) is a platform that allows users to deploy and host their own Google App Engine applications. AppScale executes automatically over [Amazon EC2](http://aws.amazon.com/ec2/) and [Eucalyptus](http://open.eucalyptus.com) as well as [Xen](http://www.xen.org) and [KVM](http://www.linux-kvm.org) and supports both the python and java Google App Engine platforms.

# Installation of [AppScale](http://appscale.cs.ucsb.edu) and KOALA #

At first you neet do install the [AppScale Tools](http://code.google.com/p/appscale/wiki/AppScale_Tools_Usage).

Pack the KOALA sourcecode into a tar.gz

```
$ cd koalacloud
$ tar -cvzf koalacloud.tar.gz . --exclude=tutorial
$ mv koalacloud.tar.gz ../
```

Start AppScale PaaS inside EC2 (this needs some time).

```
$ appscale-run-instances --file ~/workspace/koalacloud.tar.gz --table voldemort --max 2 --machine ami-044fa56d --infrastructure ec2 --keyname appscaletest -v

... lots of output here ...

New secret key is ***secret***
{"machine"=>"ami-044fa56d", "keyname"=>"appscaletest", "ips"=>"node-1--appengine:database:load_balancer:db_slave", "voldemortw"=>"2", "replication"=>"2", "instance_type"=>"m1.large", "ec2_access_key"=>"1QHSHZGENHP57C0JK582", "infrastructure"=>"ec2", "table"=>"voldemort", "min_images"=>"2", "ec2_secret_key"=>"5CP4tcnfauuyEKpW5CdgLtZvEZncOV7D9icsZCpX", "appengine"=>"3", "ec2_url"=>"https://us-east-1.ec2.amazonaws.com", "voldemortr"=>"2", "keypath"=>"appscaletest.key", "hostname"=>"ec2-184-72-184-81.compute-1.amazonaws.com", "max_images"=>"2"}
Head node successfully created at ec2-184-72-184-81.compute-1.amazonaws.com. It is now starting up voldemort via the command line arguments given.
Generating certificate and private key
Copying over credentials for cloud
Starting server at ec2-184-72-184-81.compute-1.amazonaws.com
Please wait for the controller to finish pre-processing tasks.

This AppScale instance is linked to an e-mail address giving it administrator privileges.
Enter your desired administrator e-mail address: baun@kit.edu

The new administrator password must be at least six characters long and can include non-alphanumeric characters.
Enter your new password: ***secret***
Enter again to verify: ***secret***
Please wait for AppScale to prepare your machines for use.
Spawning up 1 virtual machines
Copying over needed files and starting the AppController on the other VMs
Starting up memcached
Starting up Load Balancer
Run instances: UserAppServer is at ec2-184-72-184-81.compute-1.amazonaws.com

Your user account has been created successfully.
Uploading koalacloud...
We have reserved the name koalacloud for your application.
koalacloud was uploaded successfully.
Please wait for your app to start up.

Your app can be reached at the following URL: http://ec2-184-72-184-81.compute-1.amazonaws.com/apps/koalacloud
The status of your AppScale instance is at the following URL: http://ec2-184-72-184-81.compute-1.amazonaws.com/status
```

The AppScale instances inside EC2 are started successfully.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale14_0_amis_started_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale14_0_amis_started_small.png)

This is the status page of AppScale where you can see the AppScale instances.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale14_1_started_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale14_1_started_small.png)

When you switch to KOALA, you need to log first.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale14_2_KOALA_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale14_2_KOALA_small.png)

**Login** redirects you to the AppScale login page.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale14_3_login_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale14_3_login_small.png)

After your successful login, you can switch back to KOALA.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale14_4_login_successful_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale14_4_login_successful_small.png)

KOALA ist ready for work now. At least you need to import your credentials which is described [here](http://code.google.com/p/koalacloud/wiki/First_Steps_with_EC2_and_KOALA).

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale14_5_start_working_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale14_5_start_working_small.png)

When your AWS credentials are imported, you can manage the instances with KOALA that run KOALA and the AppScale PaaS

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale14_6_aws_inside_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale14_6_aws_inside_small.png)

This are the two AppScale instances inside EC2 that contain KOALA itself.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale14_7_redundant_view_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale14_7_redundant_view_small.png)

You can check the AppScale instances also with the command appscale-describe-instances.

```
$ appscale-describe-instances --keyname appscaletest
Status of node at ec2-184-72-184-81.compute-1.amazonaws.com:
    Currently using 6.8 Percent CPU and 10.27 Percent Memory
    Hard disk is 36 Percent full
    Is currently: load_balancer, shadow, db_master, zookeeper, login
    Database is at ec2-184-72-184-81.compute-1.amazonaws.com
    Current State: Preparing to run AppEngine apps if needed
Status of node at ec2-75-101-177-34.compute-1.amazonaws.com:
    Currently using 3.4 Percent CPU and 9.74 Percent Memory
    Hard disk is 36 Percent full
    Is currently: load_balancer, db_slave, appengine
    Database is at ec2-75-101-177-34.compute-1.amazonaws.com
    Current State: Preparing to run AppEngine apps if needed
    Hosting the following apps: koalacloud
```

To terminate the AppScale instances, you can use the command appscale-terminate-instances.

```
$ appscale-terminate-instances --infrastructure ec2 --keyname appscaletest
Not backing up data.

About to terminate instances spawned via ec2 with keyname 'appscaletest'...
Terminated AppScale in cloud deployment.
```

Alternatively you can use KOALA. :-)

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale14_8_terminate_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_koala_appscale14_8_terminate_small.png)