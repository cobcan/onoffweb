FROM python:3.10.13-slim
RUN mkdir /onoffweb
COPY onoffweb/ /onoffweb/
WORKDIR /onoffweb
RUN ls -la
RUN pip install -r requirements.txt
CMD python3 main.py
