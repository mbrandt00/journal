#!/bin/sh

# migrate database sinmce fresh docker postgres instance 

rake db:migrate 

bundle exec rspec --color --tty --format progress --format RspecJunitFormatter --out rspec.xml
