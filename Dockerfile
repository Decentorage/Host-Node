FROM python:3

# Set up code directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Install Linux dependencies
RUN apt-get update && apt-get install -y libssl-dev 

COPY ./requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

COPY . .

# Run in development enviroment
ENTRYPOINT ["python", "host.py"]
