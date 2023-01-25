# SIPin SIP Parser

## Synopsis
A service that parse and validates the unzipped SIP:
 - Parse the bag folder and validate it.
 - Parse the SIP:
   - Validate the metadata files with the corresponding XSDs.
   - Transform the SIP to a graph using SPARQL-anything and RDFLib.
   - Validate it with the respective SHACL file.

## Prerequisites

* Git
* Docker (optional)
* Python 3.10+
* Access to the meemoo PyPi

## Usage

1. Clone this repository with:

    `$ git clone https://github.com/viaacode/sipin-sip-creator.git`

2. Change into the new directory:

    `$ cd sipin-sip-creator`

3. Download [SPARQLAnything v0.8.1]([linkurl](https://github.com/SPARQL-Anything/sparql.anything/releases/download/v0.8.1/sparql-anything-0.8.1.jar)) and store it in `app/resources`.

4. Set the needed config:

Included in this repository is a config.yml file detailing the required configuration. There is also an .env.example file containing all the needed env variables used in the config.yml file. All values in the config have to be set in order for the application to function correctly. You can use !ENV ${EXAMPLE} as a config value to make the application get the EXAMPLE environment variable.

### Running locally

1. Start by creating a virtual environment:

    `$ python -m venv venv`

2. Activate the virtual environment:

    `$ source venv/bin/activate`

3. Install the external modules:

    ```
    $ pip install -r requirements.txt \
        --extra-index-url http://do-prd-mvn-01.do.viaa.be:8081/repository/pypi-all/simple \
        --trusted-host do-prd-mvn-01.do.viaa.be && \
      pip install -r requirements-dev.txt
    ```

4. Make sure to load in the ENV vars.

5. Run the tests with:

    `$ python -m pytest -v --cov=./app`

6. Run the application:

    `$ python -m main`

### Running using Docker

1. Build the container:

   `$ docker build -t sipin-sip-parser .`

2. Run the tests in a container:

    `$ docker run --env-file .env.example --rm --entrypoint python sipin-sip-parser:latest -m pytest -v --cov=./app`

3. Run the container (with specified `.env` file):

   `$ docker run --env-file .env --rm sipin-sip-parser:latest`
