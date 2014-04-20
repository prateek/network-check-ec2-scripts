#!/usr/bin/env python

import paramiko
import boto.ec2
import os
import time
import select

# TODO: extract these to a command line arg
# Parameters
access_key = os.environ["AWS_ACCESS_KEY"]
secret_key = os.environ["AWS_SECRET_KEY"]
aws_region = os.environ["AWS_REGION"]
key_name = os.environ["KEY_NAME"]
key_path = os.environ["KEY_PATH"]

def run_command(client,cmd):
  output =''
  channel = client.get_transport().open_session()
  channel.get_pty()
  channel.exec_command(cmd)
  while True:
      if channel.exit_status_ready():
          break
      rl, wl, xl = select.select([channel], [], [], 0.0)
      if len(rl) > 0:
          output = output + channel.recv(1024)
  return output

def run_server(client):
  global serverChannel
  serverChannel = client.get_transport().open_session()
  serverChannel.get_pty()
  serverChannel.exec_command('iperf3 -s')
  rl, wl, xl = select.select([serverChannel], [], [], 0.0)
  if len(rl) > 0:
    serverChannel.recv(1024)

def print_stat():
  output = ''
  while True:
    rl, wl, xl = select.select([serverChannel], [], [], 0.0)
    if len(rl) > 0:
      output = output + serverChannel.recv(1024)
    else:
      break
  if(output != ''):
    outputLines = output.splitlines()
    for lines in outputLines:
      if(lines.find('Accepted') >= 0 or lines.find('sender') >= 0 or lines.find('receiver') >= 0):
        print lines

def install_iperf3(client):
  output = run_command(client,'iperf3')
  if(output.startswith('iperf3: parameter error')):
    return
  output = run_command(client,'rm epel-release-6-8.noarch.rpm*')
  output = run_command(client,'wget http://download.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm')
  output = run_command(client,'sudo rpm -ivh epel-release-6-8.noarch.rpm')
  output = run_command(client,'sudo yum --enablerepo=epel -y install iperf3')
  output = run_command(client,'sudo /etc/init.d/iptables save')
  output = run_command(client,'sudo /etc/init.d/iptables stop')

ec2Conn = boto.ec2.connect_to_region(aws_region, aws_access_key_id = access_key, aws_secret_access_key = secret_key)
filters = {"instance-state-name":"running", "key-name":key_name}

instanceList = ec2Conn.get_only_instances(filters=filters)
print "Got instances "

#for master in instanceList[0:1]:
for master in instanceList:
  if master.state == 'running': #instance.tags.has_key('Cluster') and instance.tags['Cluster'] == 'MyCluster':
    server = paramiko.SSHClient()
    server.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    server.connect(master.ip_address,username='ec2-user',key_filename=key_path)
    install_iperf3(server)
    run_server(server)
    server_ip_addr = master.private_ip_address
    print "Server :" + master.id + " ; internal IP : " + server_ip_addr + " ; public IP : " + master.ip_address
    for instance in instanceList:
      if instance.state == 'running' and instance != master: #instance.tags.has_key('Cluster') and instance.tags['Cluster'] == 'MyCluster':
        print "Client : " + instance.id
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(instance.ip_address,username='ec2-user',key_filename=key_path)
        install_iperf3(client)
        run_command(client,'iperf3 -c '+ server_ip_addr + ' -V --set-mss 9000')
        print_stat()
        client.close()
      else:
        print "Skipping " + instance.private_ip_address
    serverChannel.close()
    server.close()

