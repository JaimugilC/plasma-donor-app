FROM python:3.6
WORKDIR /app
ADD . /app
COPY requirements.txt /app
RUN pip install -r requirements.txt
RUN pip install ibm_db
EXPOSE 5000
CMD ["python", "app.py"]