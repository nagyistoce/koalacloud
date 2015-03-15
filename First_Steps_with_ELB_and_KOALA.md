

# First steps with the KOALA Cloud Manager and ELB #

Before you start with KOALA using Amazon [Elastic Load Balancing (ELB)](http://aws.amazon.com/elb/) it is highly appreciated that you consult [this](http://code.google.com/p/koalacloud/wiki/First_Steps_with_EC2_and_KOALA) document that tells what you need to use KOALA at all and how to get your credentials inserted.

For using KOALA to interact with ELB you need access to the Amazon Web Services ([AWS](http://aws.amazon.com)) because up to now, no Private Cloud solution exists, that is API compatible with the ELB.

If you have already created an AWS account and inserted your Access Key and Secret Access Key inside the **Regions** window, you can start working with ELB when you switch to one of the four AWS regions with the pull-down menu in the center of the header.

## Elastic Load Balancing ##

With ELB, incoming traffic can be distribute across your Amazon EC2 instances that run inside a single Availability Zone or multiple Availability Zones. The instances need to run inside the same region.

You can create, alter and erase elastic load balancers at any time. It is easy to add and remove instances and rules.

## Create an Elastic Load Balancer ##

When you work the fist time with elastic load balancers, the **ELB** window will be empty. Click the button to create a new elastic load balancer inside the aktive region.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_elb_1_no_elb_yet_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_elb_1_no_elb_yet_small.png)

In the next windows you need to type in a name of the new load balancer and what availability zones inside this region shall the load balancer work for.

You also need to type in the values for the one rule. This means the internal and external port (80, 443 or 1024-65535), and the protocol (TCP or HTTP) as well.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_elb_3_create_elb2_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_elb_3_create_elb2_small.png)

The next windows shows, that the load balancer was created successfully. Now, we have a load balancer that distributes incoming traffic from port 80 via HTTP to that instances attached. There are no instances attached yet. So, we have to alter the load balancer. The screw-wrench icon leads to the next window.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_elb_4_elb_created_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_elb_4_elb_created_small.png)

In this window you can add/remove instances and availability zones to/from your load balancer.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_elb_5_alter_elb_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_elb_5_alter_elb_small.png)

Two instaces are asigned to the load balancer now.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_elb_6_instances_asigned_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_elb_6_instances_asigned_small.png)

Let's check the **ELB** window again.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_elb_7_instances_asigned2_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_elb_7_instances_asigned2_small.png)

You can add more elastic load balancers and remove existing ones at any time.