FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV APP_ENV=production
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_PORT=7860
ENV GRADIO_SHARE=false
EXPOSE 7860
CMD ["python", "app.py"]
