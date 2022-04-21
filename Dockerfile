FROM alpine

RUN apk add -U --no-cache python3 py-pip \
    adduser -S py-worker

USER py-worker

WORKDIR /home/price_indexr

RUN pip install bs4 \
    pip install requests \
    pip install sqlalchemy

ADD price_indexr.py .

ENTRYPOINT ["python3","price_indexr.py"]