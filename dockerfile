# استفاده از یک ایمیج رسمی پایتون به عنوان پایه
FROM python:3.11-slim

# تنظیم دایرکتوری کاری داخل کانتینر
WORKDIR /app

# کپی کردن فایل نیازمندی‌ها به داخل کانتینر
COPY requirements.txt .

# نصب بسته‌های مشخص شده در نیازمندی‌ها
RUN pip install --no-cache-dir -r requirements.txt

# کپی کردن بقیه کدهای برنامه به داخل کانتینر
COPY . .

# دستوری که برای اجرای برنامه استفاده می‌شود
CMD ["python", "main.py"]