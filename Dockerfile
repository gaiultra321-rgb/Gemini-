# ১. অফিশিয়াল হালকা পাইথন ইমেজ ব্যবহার করা হচ্ছে
FROM python:3.11-slim

# ২. কাজের ডিরেক্টরি সেট করা
WORKDIR /app

# ৩. প্রথমে requirements.txt কপি করা
COPY requirements.txt .

# ৪. ডিপেনডেন্সিগুলো ইন্সটল করা (ক্যাশে সেভ না করে জায়গা বাঁচানো)
RUN pip install --no-cache-dir -r requirements.txt

# ৫. প্রজেক্টের বাকি সব ফাইল (bot.py, index.html) কপি করা
COPY . .

# ৬. রেন্ডার সাধারণত একটি ডাইনামিক পোর্ট দেয়, তাই আমরা ENV ভেরিয়েবল ব্যবহার করব
ENV PORT=8000
EXPOSE $PORT

# ৭. অ্যাপটি রান করার ফাইনাল কমান্ড
CMD ["sh", "-c", "uvicorn bot:app --host 0.0.0.0 --port ${PORT:-8000}"]
