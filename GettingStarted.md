# Getting Started #

Welcome to the KOALA Cloud Manager. These Wiki-Pages can help you with your first steps while using KOALA to work with various cloud services.

## Some Facts ##

KOALA...

  * is a software service that helps you working with your Amazon Web Services (AWS) compatible cloud services. The AWS public cloud and private cloud services based on [Eucalyptus](http://open.eucalyptus.com), [Nimbus](http://www.nimbusproject.org) or [OpenNebula](http://www.opennebula.org) are supported. The storage services [Google Storage](http://code.google.com/apis/storage/) and [Host Europe Cloud Storage](http://www.hosteurope.de) can be used with KOALA too.
  * runs inside the [Google App Engine](http://appengine.google.com), [AppScale](http://appscale.cs.ucsb.edu) and [typhoonAE](http://code.google.com/p/typhoonae/)
  * is not a marketplace for cloud resources but it helps you working with cloud resources you have already access to
  * is Open Source and licensed according to the Apache License, Version 2.0
  * uses [boto](http://code.google.com/p/boto/), a Python interface to Amazon Web Services
  * uses icons from the Basic Set package from [PixelMixer](http://www.pixel-mixer.com)
  * is successfully checked with the [W3C Markup Validation Service](http://validator.w3.org) as HTML 4.01 Transitional

## What KOALA stands for ##

KOALA stands for <b>K</b>arlsruhe <b>O</b>pen <b>A</b>pplication (for) c<b>L</b>oud <b>A</b>dministration.

But the main reason for the name KOALA is, that it's easy to memorize. Furthermore [Koalas](http://en.wikipedia.org/wiki/Koala) like Eucalyptus.

Implemented features:

  * import credentials for [Amazon AWS](http://aws.amazon.com), [Eucalyptus](http://open.eucalyptus.com), [Nimbus](http://www.nimbusproject.org) and [OpenNebula](http://opennebula.org) services and infrastructures
  * switch active region
  * check availability zones
  * create and erase security groups and create and erase rules inside security groups
  * create, attach, detach and erase EBS volumes
  * create and erase snapshots from EBS volumes
  * create EBS volumes from snapshots
  * create and erase keypairs
  * check images
  * start, reboot, stop and terminate instances
  * show console output of instances
  * allocate, attach, detach and release elastic IP addresses
  * erase all personal data from the datastore
  * create image favourites (for AWS)
  * create and erase S3 buckets
  * pure S3 mode and S3 mode with more comfort
  * upload and download S3 keys and change their Access Control List
  * alter and delete elastic load balancers (ELB)

## Advantages of KOALA compared to other solutions ##

  * No local installation needed. Lokal Installation is against the cloud paradigma
  * All browsers (not only Firefox) are supported
  * Open Source
  * Support all AWS compatible Public Cloud AND Private Clouds
  * KOALA can run inside Public Clouds and Private Clouds itself

## Drawbacks of KOALA compared to other solutions ##
  * Not all features of AWS supported
  * No support from the provider of the cloud services