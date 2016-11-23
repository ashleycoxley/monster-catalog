# Monster Catalog
A catalog to view, add, edit, and delete imaginary monster descriptions and drawings: a class project for the Udacity Full Stack nanodegree.

## Running Monster Catalog

Requires Python 2.7, Vagrant, and apps registered with Facebook and Google for 3rd party oauth. 

### Vagrant setup
+ [Download VirtualBox](https://www.virtualbox.org/wiki/Downloads)
+ [Download and install Vagrant](https://www.vagrantup.com/downloads.html)

### Facebook oauth setup
+ Register at [Facebook for Developers](https://developers.facebook.com/) and create a web application
+ Store app ID and app secret in ```fb_client_secrets.json```

### Google oauth setup
+ Register at [Google Developer Console](https://console.developers.google.com/) and create a project
+ Download app credentials and add filename to ```oauth_vars.py```

### Amazon Web Services S3 setup
+ Create an AWS account at [AWS Management Console](https://aws.amazon.com/console/)
+ Create an S3 bucket
+ Create an IAM user with permissions for accessing S3
+ Add bucket name and credentials to ```monster_config_example.py``` and rename to ```monster_config.py```

### Starting the local development server
+ Clone this repository
+ From the root monster-catalog folder, run ```vagrant up```
+ ```vagrant ssh```
+ ```cd /vagrant```
+ Create database by running ```psql``` and then ```create database monstercatalog```, then disconnect by running ```\q```
+ Run ```python monster_catalog.py```
+ Interact with the site at ```http://localhost/5000```
