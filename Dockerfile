FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /LoanRepayments

COPY requirements.txt /LoanRepayments/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /LoanRepayments/

RUN chmod +x /LoanRepayments/entrypoint.sh

EXPOSE 8000

CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
