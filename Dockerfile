FROM python:3.9

WORKDIR /business-logic-service

COPY ./requirements.txt /business-logic-service/requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /business-logic-service

EXPOSE 3500

CMD ["python3", "business.py"]
