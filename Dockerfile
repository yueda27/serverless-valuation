FROM python:3.7-slim-buster
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt
ADD etc /etc
COPY handler.py /opt/valuation/
COPY report.ipynb /opt/valuation/
WORKDIR /opt/valuation
CMD python handler.py /etc/config.yml