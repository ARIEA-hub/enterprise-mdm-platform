# Step 1: Start with an official, lightweight Python blueprint image
FROM python:3.10-slim

# Step 2: Set the working directory inside the container
WORKDIR /app

# Step 3: Copy our list of dependencies into the container
COPY requirements.txt .

# Step 4: Install the required libraries inside the container
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy the rest of our python code into the container
COPY . .

# Step 6: Keep the container running idle so we can trigger it later
# CMD ["tail", "-f", "/dev/null"]
CMD ["python", "main.py"]