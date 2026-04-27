FROM python:3.12-slim
WORKDIR /web
COPY . /web
RUN pip install -r requirements.txt
EXPOSE 5000
ENV PYTHONUNBUFFERED=1
CMD ["python", "app.py"]