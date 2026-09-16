import boto3
import json

S3API = boto3.client("s3", region_name="us-east-1") 
bucket_name = "c220889a5570642l16866753t1w181870576354-s3bucket-vt3eikm03ehi"

policy_file = open("/home/ec2-user/environment/resources/public_policy.json", "r")


S3API.put_bucket_policy(
    Bucket = bucket_name,
    Policy = policy_file.read()
)
print ("Setting Permissions - DONE")