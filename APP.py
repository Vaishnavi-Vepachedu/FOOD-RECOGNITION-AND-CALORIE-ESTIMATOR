from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
from PIL import Image
import re

# Load all the environment variables
load_dotenv()

# Configure Google Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to load Google Gemini Pro Vision API and get response
def get_gemini_response(input_prompt, image):
    model = genai.GenerativeModel('gemini-pro-vision')
    response = model.generate_content([input_prompt, image[0]])
    return response.text

# Function to setup image for API input
def input_image_setup(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        image_parts = [
            {
                "mime_type": uploaded_file.type,
                "data": bytes_data
            }
        ]
        return image_parts
    else:
        raise FileNotFoundError("No file uploaded")

# Function to calculate daily calorie needs based on user profile
def calculate_daily_calorie_intake(age, sex, weight, height, activity_level):
    # Basal Metabolic Rate (BMR) calculation using Mifflin-St Jeor Equation
    if sex == "Male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # Activity level multipliers
    activity_multipliers = {
        "Sedentary": 1.2,
        "Lightly active": 1.375,
        "Moderately active": 1.55,
        "Very active": 1.725,
        "Super active": 1.9
    }

    daily_calorie_needs = bmr * activity_multipliers[activity_level]
    return daily_calorie_needs

# Initialize Streamlit app
st.set_page_config(page_title="Food Calorie Estimator", layout="centered")

# Add custom CSS for styling
st.markdown("""
    <style>
    body {
        background-color: #f4f4f9;
        font-family: 'Times new Roman', serif;
    }
    .main-header {
        background-color: #ADD8E6;
        padding: 10px;
        border-radius: 10px;
        color: black;
        text-align: center;
        font-size: 2.5em;
        font-family:'Times new roman',serif;
    }
    .file-uploader {
        border: 2px dashed #ff6347;
        border-radius: 10px;
        background-color: white;
        padding: 20px;
        text-align: center;
    }
    .file-uploader:hover {
        background-color: #f0f0f0;
    }
    .submit-button {
        background-color: #ff6347;
        color: white;
        border: none;
        padding: 15px 30px;
        border-radius: 10px;
        font-size: 1.2em;
    }
    .submit-button:hover {
        background-color: #ff4500;
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #ADD8E6;
        color: black;
        text-align: center;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# App header
st.markdown('<div class="main-header"> Food Calorie Estimator</div>', unsafe_allow_html=True)
st.write("Upload an image of your meal to get a detailed breakdown of its calorie content and healthiness.")

# User profile setup
def get_user_profile():
    st.sidebar.header("User Profile")
    name = st.sidebar.text_input("Name")
    age = st.sidebar.number_input("Age")
    sex = st.sidebar.selectbox("Sex", ["Male", "Female", "Other"])
    weight = st.sidebar.number_input("Weight (kg)", min_value=1.0, max_value=300.0)
    height = st.sidebar.number_input("Height (cm)", min_value=30.0, max_value=250.0)
    activity_level = st.sidebar.selectbox("Activity Level", ["Sedentary", "Lightly active", "Moderately active", "Very active", "Super active"])

    user_profile = {
        "name": name,
        "age": age,
        "sex": sex,
        "weight": weight,
        "height": height,
        "activity_level": activity_level
    }

    return user_profile

user_profile = get_user_profile()
daily_calorie_needs = calculate_daily_calorie_intake(user_profile["age"], user_profile["sex"], user_profile["weight"], user_profile["height"], user_profile["activity_level"])

# File uploader
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
image = None
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

# Input prompt template
input_prompt = f"""
You are an expert nutritionist analyzing an image to identify food items and estimate their calorie content.   
Here's the breakdown:  
    * List all the food items found in the image. 
    * For each item, provide the estimated number of calories and a basic health indicator (Healthy/Unhealthy). 
    * Calculate the total calorie content of all the food items combined. 
    * Include a daily recommended calorie intake range for a healthy adult with details: 
        Age: {user_profile['age']}, 
        Sex: {user_profile['sex']}, 
        Weight: {user_profile['weight']} kg, 
        Height: {user_profile['height']} cm, 
        Activity Level: {user_profile['activity_level']}.  
Output format:  
1. Item 1: [estimated calories] (Healthy/Unhealthy) 
2. Item 2: [estimated calories] (Healthy/Unhealthy) 
...
Total Calories: [total calorie content]
Daily Recommended Calorie Intake: {daily_calorie_needs:.0f} calories for a healthy adult with the specified profile.
**Remaining Recommended Calorie Intake:** [estimated remaining calories]
Finally, you can mention whether the food is healthy or not.
"""
# Helper function to parse the response and extract the total calorie count
def extract_calorie_count(response_text):
    match = re.search(r"Total Calories: (\d+)", response_text)
    if match:
        return int(match.group(1))
    return None

# Submit button
if st.button("Tell me the total calories", key="submit-button"):
    if uploaded_file is not None:
        image_data = input_image_setup(uploaded_file)
        response = get_gemini_response(input_prompt, image_data)

        st.subheader("The Response is")
        st.write(response)

        # Extract estimated calorie count from response
        estimated_calories = extract_calorie_count(response)

        if estimated_calories is not None:
            # Calculate remaining calories based on user profile
            remaining_calories = daily_calorie_needs - estimated_calories

            # Display visualization for remaining calories
            max_calories = int(daily_calorie_needs * 1.1)  # Assuming 10% buffer
            progress = int((remaining_calories / max_calories) * 100)
            st.subheader("Daily Calorie Intake Remaining")
            st.write(f"{remaining_calories:.0f} calories out of {daily_calorie_needs:.0f}")
            st.progress(progress / 100)
        else:
            st.error("Could not estimate the calories from the response.")
    else:
        st.error("Please upload an image before submitting.")

# Footer
st.markdown(
    """
    <div class="footer">
        <p>© 2024 Food Calorie Estimator. All rights reserved.</p>
    </div>
    """, unsafe_allow_html=True
)
