#!/bin/bash
set -euxv

# accepted parameters are:
# $1: driver name
# $2: driver class
# $3: author name
# $4: author email

# check if the number of parameters is correct
if [ "$#" -ne 4 ]; then
    echo "Illegal number of parameters"
    echo "Usage: create_driver.sh <driver_name> <driver_class> <author_name> <author_email>"
    echo "Example: create_driver.sh mydriver MyDriver \"John Something\" john@somewhere.com"
    exit 1
fi

export DRIVER_NAME=$1
export DRIVER_CLASS=$2
export AUTHOR_NAME=$3
export AUTHOR_EMAIL=$4


# Convert driver name to kebab case for directory name
DRIVER_NAME_KEBAB=$(echo ${DRIVER_NAME} | sed 's/_/-/g')
export DRIVER_NAME_KEBAB

# create the driver directory
DRIVER_DIRECTORY=packages/jumpstarter-driver-${DRIVER_NAME_KEBAB}
MODULE_DIRECTORY=${DRIVER_DIRECTORY}/jumpstarter_driver_${DRIVER_NAME}
# create the module directories
mkdir -p ${MODULE_DIRECTORY}
mkdir -p ${DRIVER_DIRECTORY}/examples

# Define paths
DOCS_DIRECTORY=docs/source/reference/package-apis/drivers
DOC_FILE=${DOCS_DIRECTORY}/${DRIVER_NAME_KEBAB}.md
README_FILE=${DRIVER_DIRECTORY}/README.md

# Create README.md file with initial documentation
echo "Creating README.md file: ${README_FILE}"
cat > "${README_FILE}" << 'EOF'
# ${DRIVER_CLASS} Driver

`jumpstarter-driver-${DRIVER_NAME_KEBAB}` provides functionality for interacting with ${DRIVER_NAME} devices.

## Installation

```shell
pip3 install --extra-index-url https://pkg.jumpstarter.dev/simple/ jumpstarter-driver-${DRIVER_NAME_KEBAB}
```

## Configuration

Example configuration:

```yaml
export:
  ${DRIVER_NAME}:
    type: jumpstarter_driver_${DRIVER_NAME}.driver.${DRIVER_CLASS}
    config:
      # Add required config parameters here
```

## API Reference

Add API documentation here.
EOF
# Need to expand variables after EOF to prevent early expansion
if command -v gsed &> /dev/null; then
    gsed -i "s/\${DRIVER_CLASS}/${DRIVER_CLASS}/g; s/\${DRIVER_NAME_KEBAB}/${DRIVER_NAME_KEBAB}/g; s/\${DRIVER_NAME}/${DRIVER_NAME}/g" "${README_FILE}"
elif [[ "$(uname)" == "Darwin" ]]; then
    sed -i '' "s/\${DRIVER_CLASS}/${DRIVER_CLASS}/g; s/\${DRIVER_NAME_KEBAB}/${DRIVER_NAME_KEBAB}/g; s/\${DRIVER_NAME}/${DRIVER_NAME}/g" "${README_FILE}"
else
    sed -i "s/\${DRIVER_CLASS}/${DRIVER_CLASS}/g; s/\${DRIVER_NAME_KEBAB}/${DRIVER_NAME_KEBAB}/g; s/\${DRIVER_NAME}/${DRIVER_NAME}/g" "${README_FILE}"
fi
echo "README.md file content:"
cat "${README_FILE}"

# Create symlink from documentation directory to README.md
mkdir -p ${DOCS_DIRECTORY}
echo "Creating symlink to README.md file"
rel_path=$(python3 -c "import os.path; print(os.path.relpath('${README_FILE}', '${DOCS_DIRECTORY}'))")
ln -sf "${rel_path}" "${DOC_FILE}"
echo "Created symlink: ${DOC_FILE} -> ${rel_path}"

for f in __init__.py client.py driver_test.py driver.py; do
    echo "Creating: ${MODULE_DIRECTORY}/${f}"
    envsubst < __templates__/driver/jumpstarter_driver/${f}.tmpl > ${MODULE_DIRECTORY}/${f}
done

for f in .gitignore pyproject.toml examples/exporter.yaml; do
    echo "Creating: ${DRIVER_DIRECTORY}/${f}"
    envsubst < __templates__/driver/${f}.tmpl > ${DRIVER_DIRECTORY}/${f}
done

# Add the new driver to the workspace sources in the main pyproject.toml
echo "Adding driver to workspace sources in pyproject.toml"
PACKAGE_NAME="jumpstarter-driver-${DRIVER_NAME_KEBAB}"
PYPROJECT_FILE="pyproject.toml"

# Create a temporary file to store the modified pyproject.toml
TEMP_FILE=$(mktemp)

# Read the pyproject.toml and insert the new driver in alphabetical order
python3 << EOF
import re

# Read the pyproject.toml file
with open('${PYPROJECT_FILE}', 'r') as f:
    content = f.read()

# Find the [tool.uv.sources] section
sources_pattern = r'(\[tool\.uv\.sources\]\n)(.*?)(\n\[)'
match = re.search(sources_pattern, content, re.DOTALL)

if match:
    # Get the parts: before sources section, sources content, and after sources section
    before_sources = content[:match.start()]
    sources_header = match.group(1)
    sources_content = match.group(2)
    after_sources = content[match.end(2):]
    
    # Parse existing sources
    sources = []
    for line in sources_content.strip().split('\n'):
        if line.strip() and '=' in line:
            package_name = line.split('=')[0].strip()
            sources.append((package_name, line))
    
    # Add the new driver
    new_line = '${PACKAGE_NAME} = { workspace = true }'
    sources.append(('${PACKAGE_NAME}', new_line))
    
    # Sort by package name
    sources.sort(key=lambda x: x[0])
    
    # Reconstruct the sources section
    new_sources_content = '\n'.join([line for _, line in sources])
    
    # Reconstruct the entire file
    new_content = before_sources + sources_header + new_sources_content + after_sources
    
    with open('${TEMP_FILE}', 'w') as f:
        f.write(new_content)
else:
    print("Error: Could not find [tool.uv.sources] section in pyproject.toml")
    exit(1)
EOF

# Replace the original file with the modified version
mv "${TEMP_FILE}" "${PYPROJECT_FILE}"
echo "Added ${PACKAGE_NAME} to workspace sources"
