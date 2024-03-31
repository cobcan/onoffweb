FROM python:3.10.13-slim
RUN apt-get update
RUN apt-get install iputils-ping -y
RUN mkdir /wolweb
COPY wolweb/ /wolweb/
WORKDIR /wolweb
RUN ls -la
RUN pip install -r requirements.txt
CMD python3 main.py
