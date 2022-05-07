Steps to deploy the code:

•	The check folder is used to create the docker with the following command.

 Command: docker build check

This docker images is then uploaded to AWS ecr where the lambda points to it. 

•	The SecurityCamera.py is then copied to the raspberry pi where we put the following command to start the program

Command: python3 MainRunner.py
