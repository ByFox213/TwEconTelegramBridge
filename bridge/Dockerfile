FROM python:3.11-alpine
ADD ./ /tw
WORKDIR /tw
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "-u", "/tw/bridge.py"]
