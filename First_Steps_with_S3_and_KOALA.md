This tutorial shows how KOALA can help you working with cloud services that are compatible to Amazons Simple Storage Service ([S3](http://aws.amazon.com/s3/)). S3 provides a web service based storage for applications. Several OpenSource IaaS projects provide the same functionality and implement the S3 API too.



# First steps with the KOALA Cloud Manager and S3 #

Before you start with KOALA using S3 it is highly appreciated that you consult [this](http://code.google.com/p/koalacloud/wiki/First_Steps_with_EC2_and_KOALA) document that tells what you need to use KOALA at all and how to get your credentials inserted.

For using KOALA to interact with S3 compatible cloud services you need access to at least a single cloud service that uses the API of S3.

The following table shows the cloud services available that are compatible to the S3 API.

| **S3 compatible services**                | **Private/Public Cloud** | **License**   | **Supported by KOALA** |
|:------------------------------------------|:-------------------------|:--------------|:-----------------------|
| [Amazon S3  ](http://aws.amazon.com/s3/) | Public Cloud           | proprietary | yes |
| [Google Storage](http://code.google.com/intl/de/apis/storage/)  | Public Cloud          | proprietary  | yes |
| [Host Europe Cloud Storage](http://www.hosteurope.de)  | Public Cloud          | proprietary  | yes |
| Walrus from [Eucalyptus](http://open.eucalyptus.com) | Private Cloud          | GPL v3      | yes |
| Cumulus from [Nimbus](http://www.nimbusproject.org)  | Private Cloud          | Apache License v2.0  | no |
| Object Storage _Swift_ from [OpenStack](http://openstack.org)  | Private Cloud          | Apache License v2.0  | no |

If you don't have any S3 compatible Private Cloud services running, the most easy way is to get access to [Amazon S3](http://aws.amazon.com/s3/). If you don't want this because e.g. you don't have a credit card you need a Private Cloud S3 service.

This tutorial focuses on [Amazon S3](http://aws.amazon.com/s3/) because it is the most common use case for KOALA and the Private Cloud S3 solutions have not the same level of stability and functionality.

If you have already created an AWS account and inserted your Access Key and Secret Access Key inside the **Regions** window, you can start working with [Amazon S3](http://aws.amazon.com/s3/) when you switch to one of the five AWS regions with the pull-down menu in the center of the header.

Don't fear you account or data here. No new account at the IaaS is created or data  over-written. You just import your credentials into KOALA this way.

## Buckets and Objects (Keys) ##

The _Simple_ in Simple Storage Service means not using this service is simple for the user. It means that there are just a few features provided. S3 is a simple key-based object store. Each object stores up to 5 GB, each accompanied by up to 2 KB of metadata. Additionally each object has a key assigned which is used to access the object. The service can be used via a SOAP interface and a REST interface. Bucket names and objects keys are addressable using HTTP URLs automatically:

**http://s3.amazonaws.com/bucket/key**

In [Google Storage](http://code.google.com/intl/de/apis/storage/), Bucket names and objects are also addressable using HTTP URLs following this schema:

**http://commondatastorage.googleapis.com/bucket/key**

In [Host Europe Cloud Storage](http://www.hosteurope.de), Bucket names and objects are also addressable using HTTP URLs following this schema:

**http://cs.hosteurope.de/bucket/key**

It is impossible to upload objects with KOALA into Host Europe Cloud Storage. This is because Host Europe does not support uploading objects via HTTP POST at all. More Information (in German language): http://faq.hosteurope.de/index.php?cpid=16676

Objects are stored in so called buckets and a bucket cannot include another bucket. Because S3 has a flat name space, every buckets name has be unique. This means S3 has provides nothing like directories.

Inside the **S3** window you can see a table with a list of you buckets and here you can create new buckets and erase existing ones.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_s3_1_list_of_buckets_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_s3_1_list_of_buckets_small.png)

For every bucket you have the decision to use the pure S3 mode and a S3 mode with more comfort. The pure S3 mode presents the contend of the buckets exactly the way it is. Just the objects inside the bucket are printed out.

The S3 mode with more comfort simulates folders with clever use of key names. Here, keys that end with **`_`$folder$** are used as directory placeholders. A key that is meant staying inside are folder has a name following this schema **folder/subfolder/filename**. It is the same approach the famous Firefox plugin [S3Fox](http://www.s3fox.net) uses.

## Pure S3 mode ##

When jumped into a bucket for the first time in the pure S3 mode, the bucket is still empty.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_s3_2_pure_s3_mode_inside_bucket_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_s3_2_pure_s3_mode_inside_bucket_small.png)

With the HTML form it is easy to upload files into the bucket. Beside the file itself you have to chose the access rights, called Access Controll List, of the object and the mime type.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_s3_3_upload_key_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_s3_3_upload_key_small.png)

After the successful upload the object is listed inside the bucket.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_s3_4_key_is_uploaded_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_s3_4_key_is_uploaded_small.png)

The table that contains the objects inside the bucket, allows to open and erase objects and change the Access Controll List (ACL).

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_s3_5_change_ACL_of_key_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_s3_5_change_ACL_of_key_small.png)

## S3 mode with more comfort ##

When jumped into a bucket in the S3 mode with more comfort, you can see a new HTML form that allows to create folders. These are emulated via the keyname as described before. In the table it's easy to differentiate between standard keys and keys that emulate folders. Icons before the keyname show the objects designation. Folders can be erased and their ACL can be alterd the same way like objects with standard keys.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_s3_6_s3_mode_with_more_comfort_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_s3_6_s3_mode_with_more_comfort_small.png)

You can jump into folders and upload objects into these folders.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_s3_7_folder_created_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_s3_7_folder_created_small.png)

It's also possible to create subfolders. And with the green arrow it's easy to jump back in the emulated filesystem hierarchy.

![http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_s3_8_subfolder_small.png](http://koalacloud.googlecode.com/svn/trunk/tutorial/images/smaller/tutorial_s3_8_subfolder_small.png)

For a deeper look how the S3 mode with more comfort works it's a good idea to creating some folders and subfolders with some objects and check the content of the bucket via the pure S3 mode.