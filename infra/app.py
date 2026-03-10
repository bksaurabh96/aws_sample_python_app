#!/usr/bin/env python3

import aws_cdk as cdk
from aws_sample_python_app_stack import AwsSamplePythonAppStack

app = cdk.App()
AwsSamplePythonAppStack(app, "AwsSamplePythonAppStack")

app.synth()