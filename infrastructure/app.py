#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stack.journal_stack import JournalStack
from stack.journal_stack import generateResourceName

app = cdk.App()
JournalStack(
    app,
    generateResourceName("stack"),
    env=cdk.Environment(
        account=os.getenv('AWS_ACCOUNT_ID'),
        region=os.getenv('AWS_REGION')
    )
)

app.synth()
