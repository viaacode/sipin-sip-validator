FROM python:3.10-slim

# Install OpenJDK-17 and wget
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk-headless wget && \
    apt-get clean;

# Set Java path.
ENV JAVA_HOME /usr/lib/jvm/java-17-openjdk-amd64/
ENV PATH $JAVA_HOME/bin:$PATH

# Download pysparql_anything in correct folder.
RUN mkdir /usr/local/lib/python3.10/site-packages/pysparql_anything/ && \
    wget -O /usr/local/lib/python3.10/site-packages/pysparql_anything/sparql-anything-v0.8.2.jar https://github.com/SPARQL-Anything/sparql.anything/releases/download/v0.8.2/sparql-anything-0.8.2.jar 

# Make a new group and user so we don't run as root.
RUN addgroup --system appgroup && adduser --system appuser --ingroup appgroup

WORKDIR /app


# Let the appuser own the files so he can rwx during runtime.
COPY . .
RUN chown -R appuser:appgroup /app

# We install all our Python dependencies. Add the extra index url because some
# packages are in the meemoo repo.
RUN pip3 install -r requirements.txt \
    --extra-index-url http://do-prd-mvn-01.do.viaa.be:8081/repository/pypi-all/simple \
    --trusted-host do-prd-mvn-01.do.viaa.be &&\
    pip3 install -r requirements-dev.txt

USER appuser

# This command will be run when starting the container. It is the same one that can be used to run the application locally.
CMD [ "python", "main.py"]