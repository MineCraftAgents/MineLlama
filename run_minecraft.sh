#!/bin/bash

# Navigate to the forge-1 directory
# cd /Users/drp2024/Desktop/forge-1
cd forge-1
# Add Gradle to the PATH
export PATH=$PATH:/opt/gradle/gradle-8.1.1/bin

# Display Gradle version
gradle -v

# Build the project
gradle build

# Run the Minecraft client
gradle runclient
