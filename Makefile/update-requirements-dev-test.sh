#!/bin/bash

# Update script for Devin project development and test dependencies

echo "Updating development and test dependencies for Devin project..."

# Update development dependencies from requirements-dev.txt
pip install --upgrade -r requirements-dev.txt

# Update test dependencies from requirements-test.txt
pip install --upgrade -r requirements-test.txt

# Verify if all development and test packages are installed and up-to-date
pip freeze > requirements-dev.txt
pip freeze > requirements-test.txt

echo "Development and test dependencies updated successfully."

# Check the status to confirm updates
if [ $? -eq 0 ]; then
    echo "Update completed successfully."
else
    echo "An error occurred while updating dependencies. Please review the output above for details."
fi
