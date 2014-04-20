# Network Check Scripts #

A script to check the network latency between all pairs of EC2 hosts. It can be used to check if the nodes are within the same placement group. 

The script assumes that all the nodes to be tested are provisioned using the same keypair, and no other nodes are provisioned using that keypair.

## Usage Notes ##

1. Fill in the appropriate values in `setEnv.sh` 
```sh
export AWS_ACCESS_KEY=INSERT_HERE
export AWS_SECRET_KEY=INSERT_HERE
export AWS_REGION=INSERT_HERE
export KEY_NAME=INSERT_HERE
export KEY_PATH=INSERT_HERE
```

2. run `setEnv.sh`

3. run `iperf3Test.py`

4. Profit!
