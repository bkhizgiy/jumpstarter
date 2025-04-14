*** Settings ***
Library     String
Library     jumpstarter_robotframework.JumpstarterLibrary


*** Test Cases ***
Example Test Case
    Acquire Lease    selector=example.com/board=qemu
    Power On
    Release Lease
